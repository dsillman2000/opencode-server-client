"""Core type definitions for OpenCode server client.

This module defines the data models used throughout the library, including
session metadata, messages, status information, and event types.
"""

from dataclasses import dataclass, field
from typing import Literal, Union, Optional, List, Dict, Any
from datetime import datetime


@dataclass
class SessionMetadata:
    """Metadata about an OpenCode session.

    Attributes:
        session_id: Unique identifier for the session
        created_at: Timestamp when the session was created
        last_activity: Timestamp of last activity in the session
        workdir: Working directory context for the session
    """

    session_id: str
    created_at: datetime
    last_activity: datetime
    workdir: str


@dataclass
class UserMessage:
    """A message from the user in a session.

    Attributes:
        content: The text content of the message
        timestamp: When the message was sent
        message_id: Unique identifier for this message
    """

    content: str
    timestamp: datetime
    message_id: Optional[str] = None


@dataclass
class AssistantMessage:
    """A message from the assistant (OpenCode) in a session.

    Attributes:
        content: The text content of the message
        timestamp: When the message was generated
        message_id: Unique identifier for this message
    """

    content: str
    timestamp: datetime
    message_id: Optional[str] = None


@dataclass
class WorktreeMetadata:
    """Metadata about a worktree (project directory).

    Attributes:
        path: Absolute path to the worktree
        name: Human-readable name for the worktree
        git_repo: Whether this is a git repository
        python_version: Python version used in this worktree
    """

    path: str
    name: str
    git_repo: bool
    python_version: Optional[str] = None


# Session status type - can be idle, busy, or in retry state
SessionStatus = Union[Literal["idle"], Literal["busy"], Literal["retry"]]


@dataclass
class SessionStatusEvent:
    """Event indicating a change in session status.

    Attributes:
        session_id: ID of the session
        status: New status of the session
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
class MessageUpdatedEvent:
    """Event indicating a message was updated.

    Attributes:
        session_id: ID of the session containing the message
        message_id: ID of the message
        content: Updated message content
        timestamp: When the update occurred
    """

    session_id: str
    message_id: str
    content: str
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
    timestamp: Optional[datetime] = field(default_factory=datetime.now)
