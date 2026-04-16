"""EventParser for converting raw SSE data to typed event objects.

This module provides parsing logic for Server-Sent Events (SSE) from the
/global/event endpoint. It handles JSON deserialization, validation, and
conversion to typed Python dataclasses.

The parser is shared between sync and async event subscription layers.

Examples:
    >>> parser = EventParser()
    >>> raw_sse = b'event: session.idle\\ndata: {"session_id": "abc123", "timestamp": "2024-04-15T10:00:00Z"}'
    >>> event = parser.parse(raw_sse)
    >>> if isinstance(event, SessionIdleEvent):
    ...     print(f"Session {event.session_id} is idle")
"""

import json
import logging
from datetime import datetime
from typing import Optional

from opencode_server_client.events.types import (
    AnyEvent,
    MessagePartDeltaEvent,
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    ServerConnectedEvent,
    ServerHeartbeatEvent,
    SessionDiffEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionStatusEvent,
    SessionUpdatedEvent,
)

logger = logging.getLogger(__name__)


class EventParser:
    """Parse raw SSE data into typed event objects.

    The SSE format expected is:
        event: <event_type>
        data: <json_payload>

    Supported event types:
        - session.status: SessionStatusEvent
        - session.idle: SessionIdleEvent
        - session.updated: SessionUpdatedEvent
        - session.diff: SessionDiffEvent
        - session.error: SessionErrorEvent
        - server.heartbeat: ServerHeartbeatEvent
        - server.connected: ServerConnectedEvent
        - message.updated: MessageUpdatedEvent
        - message.part.updated: MessagePartUpdatedEvent
        - message.part.delta: MessagePartDeltaEvent
    """

    def parse(self, raw_sse_data: bytes) -> Optional[AnyEvent]:
        """Parse raw SSE data into a typed event object.

        Args:
            raw_sse_data: Raw SSE data as bytes (from httpx stream)

        Returns:
            Typed event object (SessionIdleEvent, MessageUpdatedEvent, etc.)
            or None if event type is unknown or data is invalid

        Raises:
            ValueError: If JSON data is malformed or missing required fields
        """
        try:
            # Decode the bytes to string
            data_str = raw_sse_data.decode("utf-8", errors="replace").strip()

            if not data_str:
                return None

            # Parse the SSE format: event type and data are separate lines
            lines = data_str.split("\n")
            event_type = None
            event_properties = None

            for line in lines:
                json_payload = json.loads(line.strip())
                directory = json_payload.get("directory")
                payload = json_payload.get("payload")
                event_type = payload.get("type")
                event_properties = payload.get("properties", {})

            if not event_type:
                logger.warning(f"Missing event type or properties in SSE: {data_str}")
                return None

            # Convert JSON to event based on type
            return self._convert_to_event(event_type, event_properties)

        except Exception as e:
            logger.error(f"Error parsing SSE data: {raw_sse_data}", exc_info=e)
            raise

    def _convert_to_event(self, event_type: str, data: dict) -> Optional[AnyEvent]:
        """Convert JSON data to typed event based on event_type.

        Args:
            event_type: The event type string (e.g., "session.idle")
            data: Parsed JSON data dict

        Returns:
            Typed event object or None if event type is unknown

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Helper to parse ISO timestamp or Unix timestamp
            def parse_timestamp(ts: any) -> datetime:
                if isinstance(ts, str):
                    # Try ISO format first
                    try:
                        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except ValueError:
                        # Fall back to Unix timestamp
                        return datetime.fromtimestamp(float(ts) / 1000)
                elif isinstance(ts, (int, float)):
                    # Unix timestamp in milliseconds or seconds
                    if ts > 10000000000:  # Likely milliseconds
                        return datetime.fromtimestamp(ts / 1000)
                    else:  # Likely seconds
                        return datetime.fromtimestamp(ts)
                return datetime.now()

            # Helper to validate required fields
            def check_required(field_name: str, _data=data) -> str:
                if field_name not in _data or _data[field_name] is None:
                    raise ValueError(
                        f"Missing required field for '{event_type}': {field_name}\n{_data}"
                    )
                return _data[field_name]

            if event_type == "session.status":
                return SessionStatusEvent(
                    session_id=check_required("sessionID"),
                    status=check_required("status"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "session.idle":
                return SessionIdleEvent(
                    session_id=check_required("sessionID"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "session.updated":
                return SessionUpdatedEvent(
                    session_id=check_required("sessionID"),
                    info=check_required("info"),
                    timestamp=parse_timestamp(
                        data.get("time", datetime.now().isoformat())
                    ),
                )

            elif event_type == "message.updated":
                return MessageUpdatedEvent(
                    session_id=check_required("sessionID"),
                    message_id=check_required("id", check_required("info", data)),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "message.part.updated":
                part = check_required("part")
                # messageID can be at top level or inside part object
                message_id = data.get("messageID") or part.get("messageID")
                if not message_id:
                    raise ValueError(
                        f"Missing required field: messageID not found at top level or in part object"
                    )
                return MessagePartUpdatedEvent(
                    session_id=check_required("sessionID"),
                    message_id=message_id,
                    part_id=part.get("id", ""),
                    part=part,
                    timestamp=parse_timestamp(
                        data.get("time", datetime.now().isoformat())
                    ),
                )

            elif event_type == "message.part.delta":
                return MessagePartDeltaEvent(
                    session_id=check_required("sessionID"),
                    message_id=check_required("messageID"),
                    part_id=check_required("partID"),
                    field=check_required("field"),
                    delta=check_required("delta"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "session.error":
                # Handle both formats: error_message at top level or nested in error object
                error_message = data.get("error_message")
                error_code = data.get("error_code")
                if not error_message and "error" in data:
                    error_obj = data.get("error", {})
                    if isinstance(error_obj, dict):
                        error_message = error_obj.get("data", {}).get(
                            "message"
                        ) or error_obj.get("name")
                        # Get error code from nested error object if not at top level
                        if not error_code:
                            error_code = error_obj.get("name")

                if not error_message:
                    raise ValueError(
                        "Missing error_message: not found at top level or in error object"
                    )

                return SessionErrorEvent(
                    session_id=check_required("sessionID"),
                    error_message=error_message,
                    error_code=error_code,
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "server.heartbeat":
                # Heartbeat events have no required data, just a timestamp
                return ServerHeartbeatEvent(
                    timestamp=parse_timestamp(
                        data.get("time", datetime.now().isoformat())
                    ),
                )

            elif event_type == "session.diff":
                return SessionDiffEvent(
                    session_id=check_required("sessionID"),
                    diff=data.get("diff", []),
                    timestamp=parse_timestamp(
                        data.get("time", datetime.now().isoformat())
                    ),
                )

            elif event_type == "server.connected":
                # Server connected event has no required data, just a timestamp
                return ServerConnectedEvent(
                    timestamp=parse_timestamp(
                        data.get("time", datetime.now().isoformat())
                    ),
                )

            else:
                logger.warning(f"Unknown event type: {event_type} with data: {data}")
                return None

        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error converting event data: {data}", exc_info=e)
            raise ValueError(
                f"Missing or invalid field in event type '{event_type}': {e}"
            ) from e
