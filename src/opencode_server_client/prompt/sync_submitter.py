"""Prompt submission for sending prompts to OpenCode sessions.

This module provides the PromptSubmitter class which handles submitting
prompts/messages to sessions and managing session abortion.

Typical usage:
    >>> from opencode_server_client.prompt.sync_submitter import PromptSubmitter
    >>> submitter = PromptSubmitter(http_client)
    >>> result = submitter.submit_prompt(
    ...     session_id="abc123",
    ...     text="What is the file structure?",
    ...     provider_id="nvidia",
    ...     model_id="nim",
    ...     abort=True  # abort current processing first
    ... )
    >>> print(f"Message ID: {result['message_id']}")
"""

import logging
from typing import Any, Dict, Optional

from opencode_server_client.http_client.sync_client import SyncHttpClient
from opencode_server_client.identifiers import generate_message_id, generate_part_id

logger = logging.getLogger(__name__)


class _PromptPayload(dict):
    """Strict prompt_async payload with legacy alias access.

    The actual serialized payload remains SSE-first and only contains
    the valid wire keys, but tests and older callers can still read
    `text` and `message_id` as computed aliases.
    """

    def __contains__(self, key: object) -> bool:
        if key in {"text", "message_id"}:
            return True
        return super().__contains__(key)

    def __getitem__(self, key: str) -> Any:
        if key == "text":
            parts = super().__getitem__("parts")
            for part in parts:
                if part.get("type") == "text":
                    return part.get("text")
            raise KeyError(key)
        if key == "message_id":
            return super().__getitem__("messageID")
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


class PromptSubmitter:
    """Submit prompts and manage session abortion via HTTP API.

    This class handles:
    - Submitting prompts/messages to sessions
    - Optional abort-before-submit logic
    - Session abortion

    Attributes:
        http_client: SyncHttpClient instance for HTTP requests
    """

    def __init__(self, http_client: SyncHttpClient):
        """Initialize the PromptSubmitter.

        Args:
            http_client: SyncHttpClient instance for making requests
        """
        self.http_client = http_client

    def submit_prompt(
        self,
        session_id: str,
        text: str,
        message_id: Optional[str] = None,
        agent: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
        abort: bool = False,
        directory: Optional[str] = None,
    ) -> str:
        """Submit a prompt to a session.

        Args:
            session_id: ID of the session
            text: Prompt text to send
            message_id: Optional message ID (auto-generated if not provided)
            agent: Optional agent name/config
            system_prompt: Optional system prompt override
            tools: Optional tools configuration
            provider_id: Optional provider ID (e.g., "anthropic", "openai")
            model_id: Optional model ID (e.g., "opus-4.6", "gpt-5.4")
            abort: If True, abort session before submitting (default: False)
            directory: Optional directory context

        Returns:
            (str) The ID of the submitted message.

        Raises:
            PromptSubmissionError: If submission fails
            SessionNotFoundError: If session not found
        """
        # Generate message_id if not provided
        if not message_id:
            message_id = generate_message_id()

        # Abort first if requested
        if abort:
            try:
                self.abort_session(session_id, directory=directory)
            except Exception as e:
                logger.warning(f"Failed to abort session during submit: {e}")
                # Continue with submission anyway

        # Build the strict SSE-first wire payload expected by prompt_async.
        payload = _PromptPayload(
            {
                "parts": [{"type": "text", "text": text, "id": generate_part_id()}],
                "messageID": message_id,
            }
        )

        if agent:
            payload["agent"] = agent
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if tools:
            payload["tools"] = tools
        if provider_id or model_id:
            payload["model"] = {}
            if provider_id:
                payload["model"]["providerID"] = provider_id
            if model_id:
                payload["model"]["modelID"] = model_id

        try:
            response = self.http_client.post(
                f"/session/{session_id}/prompt_async",
                json=payload,
                directory=directory,
            )
            response.raise_for_status()
            # Should raise a 204 No Content if successful.
            return message_id
        except Exception as e:
            logger.error(f"Failed to submit prompt to session {session_id}: {e}")
            raise

    def abort_session(
        self,
        session_id: str,
        directory: Optional[str] = None,
    ) -> None:
        """Abort current processing in a session.

        Args:
            session_id: ID of the session to abort
            directory: Optional directory context

        Raises:
            SessionNotFoundError: If session not found (404)
            PromptSubmissionError: If abortion fails
        """
        try:
            response = self.http_client.post(
                f"/session/{session_id}/abort",
                directory=directory,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to abort session {session_id}: {e}")
            raise
