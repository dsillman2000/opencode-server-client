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
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionStatusEvent,
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
        - message.updated: MessageUpdatedEvent
        - message.part_updated: MessagePartUpdatedEvent
        - session.error: SessionErrorEvent
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
            json_data = None

            for line in lines:
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    json_str = line[5:].strip()
                    try:
                        json_data = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Invalid JSON in SSE data: {json_str}", exc_info=e
                        )
                        raise ValueError(f"Invalid JSON in event data: {e}") from e

            if not event_type or not json_data:
                logger.warning(f"Missing event type or data in SSE: {data_str}")
                return None

            # Convert JSON to event based on type
            return self._convert_to_event(event_type, json_data)

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
            # Helper to parse ISO timestamp
            def parse_timestamp(ts_str: str) -> datetime:
                if isinstance(ts_str, str):
                    # Try ISO format first
                    try:
                        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        # Fall back to Unix timestamp
                        return datetime.fromtimestamp(float(ts_str))
                return datetime.fromtimestamp(float(ts_str))

            # Helper to validate required fields
            def check_required(field_name: str):
                if field_name not in data or data[field_name] is None:
                    raise ValueError(f"Missing required field: {field_name}")
                return data[field_name]

            if event_type == "session.status":
                return SessionStatusEvent(
                    session_id=check_required("session_id"),
                    status=check_required("status"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "session.idle":
                return SessionIdleEvent(
                    session_id=check_required("session_id"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "message.updated":
                return MessageUpdatedEvent(
                    session_id=check_required("session_id"),
                    message_id=check_required("message_id"),
                    content=check_required("content"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "message.part_updated":
                return MessagePartUpdatedEvent(
                    session_id=check_required("session_id"),
                    message_id=check_required("message_id"),
                    part_index=int(data.get("part_index", 0)),
                    content=check_required("content"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            elif event_type == "session.error":
                return SessionErrorEvent(
                    session_id=check_required("session_id"),
                    error_message=check_required("error_message"),
                    error_code=data.get("error_code"),
                    timestamp=parse_timestamp(
                        data.get("timestamp", datetime.now().isoformat())
                    ),
                )

            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None

        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error converting event data: {data}", exc_info=e)
            raise ValueError(f"Missing or invalid field in event: {e}") from e
