"""Event types and parsing for real-time Server-Sent Events (SSE).

This module provides:
- Event type definitions (SessionIdleEvent, MessageUpdatedEvent, etc.)
- EventParser for converting raw SSE to typed events
- EventSubscriber for sync event subscription (background thread)
- Shared infrastructure for both sync and async event subscription

Typical usage:
    >>> from opencode_server_client.events import SessionIdleEvent, EventParser, EventSubscriber
    >>> parser = EventParser()
    >>> subscriber = EventSubscriber(http_client)
"""

from opencode_server_client.events.parser import EventParser
from opencode_server_client.events.sync_subscriber import EventSubscriber
from opencode_server_client.events.types import (
    AnyEvent,
    MessagePartDeltaEvent,
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionStatus,
    SessionStatusEvent,
    SessionUpdatedEvent,
)

__all__ = [
    "EventParser",
    "EventSubscriber",
    "SessionStatusEvent",
    "SessionIdleEvent",
    "MessageUpdatedEvent",
    "MessagePartUpdatedEvent",
    "SessionUpdatedEvent",
    "MessagePartDeltaEvent",
    "SessionErrorEvent",
    "SessionStatus",
    "AnyEvent",
]
