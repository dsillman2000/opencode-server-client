"""Event type definitions for Server-Sent Events (SSE).

This module defines the event types that are shared between sync and async
event subscription layers. Events are emitted by the server via /global/event
endpoint and represent real-time changes in session state.

Shared event types:
- SessionStatusEvent: Session status changed (idle/busy/error)
- SessionIdleEvent: Session transitioned to idle state
- SessionUpdatedEvent: Session metadata updated
- MessageUpdatedEvent: Message content updated in a session
- MessagePartUpdatedEvent: Partial message update (streaming content)
- MessagePartDeltaEvent: Incremental delta for message part content
- SessionErrorEvent: Error occurred in session

Examples:
    >>> from opencode_server_client.events.types import SessionIdleEvent
    >>> event = SessionIdleEvent(session_id="abc123", timestamp=datetime.now())
    >>> print(f"Session {event.session_id} is now idle")
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, Union

# Session status type - can be idle, busy, or in retry state
SessionStatus = Union[
    Literal["idle"], Literal["busy"], Literal["retry"], Literal["error"]
]


@dataclass
class SessionStatusEvent:
    """Event indicating a change in session status.

    Attributes:
        session_id: ID of the session
        status: New status of the session (idle/busy/retry/error)
        timestamp: When the status changed
    """

    session_id: str
    status: SessionStatus
    timestamp: datetime


@dataclass
class SessionIdleEvent:
    """Event indicating a session became idle.

    Attributes:
        session_id: ID of the session
        timestamp: When the session became idle
    """

    session_id: str
    timestamp: datetime


@dataclass
class SessionUpdatedEvent:
    """Event indicating session metadata was updated.

    Attributes:
        session_id: ID of the session
        info: Updated session information dict
        timestamp: When the update occurred
    """

    session_id: str
    info: dict
    timestamp: datetime


@dataclass
class MessageUpdatedEvent:
    """Event indicating a message was updated or created.

    Attributes:
        session_id: ID of the session containing the message
        message_id: ID of the message
        content: Updated message content
        timestamp: When the update occurred
    """

    session_id: str
    message_id: str
    timestamp: datetime


@dataclass
class MessagePartUpdatedEvent:
    """Event indicating a partial message update (streaming content).

    Used for streaming responses where content arrives incrementally.

    Attributes:
        session_id: ID of the session containing the message
        message_id: ID of the message
        part_id: ID of this message part
        part: Part data dict containing type, content, etc.
        timestamp: When the update occurred
    """

    session_id: str
    message_id: str
    part_id: str
    part: dict
    timestamp: datetime


@dataclass
class MessagePartDeltaEvent:
    """Event indicating an incremental delta for message part content.

    Used for streaming text responses where delta updates arrive.

    Attributes:
        session_id: ID of the session containing the message
        message_id: ID of the message
        part_id: ID of this message part
        field: Field being updated (e.g., "text")
        delta: The incremental change to the field
        timestamp: When the update occurred
    """

    session_id: str
    message_id: str
    part_id: str
    field: str
    delta: str
    timestamp: datetime


@dataclass
class SessionErrorEvent:
    """Event indicating an error occurred in a session.

    Attributes:
        session_id: ID of the session
        error_message: Description of the error
        error_code: Optional error code
        timestamp: When the error occurred
    """

    session_id: str
    error_message: str
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServerHeartbeatEvent:
    """Heartbeat event sent by the server to keep connection alive.

    Attributes:
        timestamp: When the heartbeat was sent
    """

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionDiffEvent:
    """Event indicating session state diff/changes.

    Attributes:
        session_id: ID of the session
        diff: List of changes/diffs (can be empty)
        timestamp: When the diff occurred
    """

    session_id: str
    diff: list = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServerConnectedEvent:
    """Server connection established event.

    Attributes:
        timestamp: When the connection was established
    """

    timestamp: datetime = field(default_factory=datetime.now)


# Type alias for any event that could come from the SSE stream
AnyEvent = Union[
    SessionStatusEvent,
    SessionIdleEvent,
    SessionUpdatedEvent,
    MessageUpdatedEvent,
    MessagePartUpdatedEvent,
    MessagePartDeltaEvent,
    SessionErrorEvent,
    ServerHeartbeatEvent,
    SessionDiffEvent,
    ServerConnectedEvent,
]
