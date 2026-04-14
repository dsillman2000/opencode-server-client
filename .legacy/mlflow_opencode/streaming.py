"""Streaming prompt execution for Opencode."""

import json
import time
import uuid
from typing import Any, Optional

import httpx
import mlflow
from mlflow.entities import SpanEvent


def _new_id(prefix: str = "", hyphens: bool = False) -> str:
    """Generate a new unique ID."""
    id_str = str(uuid.uuid4())
    if not hyphens:
        id_str = id_str.replace("-", "")
    return f"{prefix}{id_str}"


class StreamingPrompt:
    """Manages streaming prompt execution and message collection."""

    def __init__(
        self,
        client: httpx.Client,
        session_id: str,
        model: str,
        prompt: str,
    ):
        """Initialize streaming prompt.

        Args:
            client: httpx.Client configured for Opencode API
            session_id: Session ID to run prompt in
            model: Model ID to use
            prompt: Prompt text to send
        """
        self.client = client
        self.session_id = session_id
        self.model = model
        self.prompt = prompt
        self._prompt_message_id = _new_id(prefix="msg_")
        self._response_messages: list[dict[str, Any]] = []
        self._latest_assistant_message: dict[str, Any] = {}
        self._assistant_text = ""
        self._baseline_assistant_ids: set[str] = set()
        self._seen_part_keys: set[tuple[str, int]] = set()
        self._ordered_parts: list[dict[str, Any]] = []

    def __enter__(self):
        """Enter streaming context and start prompt execution."""
        baseline_resp = self.client.get(f"/session/{self.session_id}/message")
        baseline_resp.raise_for_status()
        baseline_messages = baseline_resp.json()
        self._baseline_assistant_ids = {
            m.get("info", {}).get("id")
            for m in baseline_messages
            if m.get("info", {}).get("role") == "assistant" and m.get("info", {}).get("id")
        }

        response = self.client.post(
            f"/session/{self.session_id}/prompt_async",
            json={
                "messageID": self._prompt_message_id,
                "agent": "build",
                "model": {"providerID": "nvidia", "modelID": self.model},
                "parts": [{"type": "text", "text": self.prompt, "id": _new_id(prefix="prt_")}],
            },
        )
        response.raise_for_status()
        self.refresh_messages()
        return self

    def refresh_messages(self):
        """Fetch latest messages from session."""
        resp = self.client.get(f"/session/{self.session_id}/message")
        resp.raise_for_status()
        messages = resp.json()

        assistant_messages = [
            m
            for m in messages
            if m.get("info", {}).get("role") == "assistant"
            and m.get("info", {}).get("id") not in self._baseline_assistant_ids
        ]

        text_parts: list[str] = []
        ordered_parts: list[dict[str, Any]] = []
        for message in assistant_messages:
            message_id = message.get("info", {}).get("id", "unknown")
            for part_index, part in enumerate(message.get("parts", [])):
                ordered_parts.append(part)
                if part.get("type") == "text" and part.get("text"):
                    text_parts.append(part["text"])

                part_key = (message_id, part_index)
                if part_key in self._seen_part_keys:
                    continue

                self._seen_part_keys.add(part_key)
                if self._is_non_trivial_part(part):
                    self._ordered_parts.append(part)
                    self._emit_part_event(message_id, part_index, part)

        self._assistant_text = "\n".join(text_parts)

        if assistant_messages:
            self._latest_assistant_message = assistant_messages[-1]
            if not self._response_messages or self._latest_assistant_message.get("info", {}).get(
                "id"
            ) != self._response_messages[-1].get("info", {}).get("id"):
                self._response_messages.append(self._latest_assistant_message)
            else:
                self._response_messages[-1] = self._latest_assistant_message

        return self._response_messages

    @staticmethod
    def _is_non_trivial_part(part: dict[str, Any]) -> bool:
        """Return True when a streamed part should be recorded on the turn span."""
        part_type = str(part.get("type", "")).lower()
        if part_type == "text":
            return bool(str(part.get("text", "")).strip())
        return "tool" in part_type or "reason" in part_type

    @staticmethod
    def _event_name_for_part(part: dict[str, Any]) -> Optional[str]:
        """Map a streamed part to a span event name."""
        part_type = str(part.get("type", "")).lower()
        if part_type == "text":
            return "text_part"
        if "tool" in part_type:
            return "tool_call_part"
        if "reason" in part_type:
            return "reasoning_part"
        return None

    @staticmethod
    def _render_part(part: dict[str, Any]) -> str:
        """Render a streamed part for concatenated message output."""
        part_type = str(part.get("type", "text"))
        if part_type == "text":
            return str(part.get("text", "")).strip()

        if "reason" in part_type.lower() and part.get("text"):
            return f"[{part_type}] {str(part['text']).strip()}"

        return f"[{part_type}] {json.dumps(part, sort_keys=True)}"

    def _emit_part_event(self, message_id: str, part_index: int, part: dict[str, Any]) -> None:
        """Emit a streamed part as an event on the active chat turn span."""
        event_name = self._event_name_for_part(part)
        if not event_name:
            return

        active_span = mlflow.get_current_active_span()
        if active_span is None:
            return

        active_span.add_event(
            SpanEvent(
                name=event_name,
                attributes={
                    "message_id": message_id,
                    "part_index": part_index,
                    "part_type": str(part.get("type", "unknown")),
                    "content": self._render_part(part),
                },
            )
        )

    def concatenated_parts_message(self) -> str:
        """Return a final concatenated assistant message including all recorded parts."""
        rendered_parts = [self._render_part(part) for part in self._ordered_parts]
        return "\n\n".join(part for part in rendered_parts if part)

    def turn_output(self) -> dict[str, Any]:
        """Return structured output for the current chat turn span."""
        return {
            "assistant_text": self._assistant_text,
            "assistant_message_with_parts": self.concatenated_parts_message(),
        }

    def abort(self) -> None:
        """Abort the currently running prompt for this session."""
        active_span = mlflow.get_current_active_span()
        if active_span is not None:
            active_span.add_event(SpanEvent(name="chat_turn_abort_requested", attributes={}))

        resp = self.client.post(f"/session/{self.session_id}/abort")
        resp.raise_for_status()

        if active_span is not None:
            active_span.add_event(SpanEvent(name="chat_turn_aborted", attributes={}))

    def finished(self) -> bool:
        """Check if streaming is finished."""
        parts = self._latest_assistant_message.get("parts", [])
        return any(part.get("type") == "step-finish" for part in parts)

    def assistant_text(self) -> str:
        """Get accumulated assistant text."""
        return self._assistant_text

    def latest_message_id(self) -> Optional[str]:
        """Get ID of latest assistant message."""
        return self._latest_assistant_message.get("info", {}).get("id")

    def latest_message(self) -> dict[str, Any]:
        """Get latest assistant message object."""
        return self._latest_assistant_message

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit streaming context."""
        return None
