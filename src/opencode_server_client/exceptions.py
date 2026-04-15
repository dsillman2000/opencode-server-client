"""Exception hierarchy for OpenCode server client.

All exceptions raised by the library inherit from OpencodeError.
"""


class OpencodeError(Exception):
    """Base exception for all OpenCode client errors."""

    pass


class SessionError(OpencodeError):
    """Base exception for session-related errors."""

    pass


class SessionCreationError(SessionError):
    """Raised when a session cannot be created."""

    pass


class SessionNotFoundError(SessionError):
    """Raised when a session with the given ID cannot be found."""

    pass


class PromptSubmissionError(OpencodeError):
    """Raised when a prompt cannot be submitted."""

    pass


class WorktreeError(OpencodeError):
    """Raised when a worktree operation fails."""

    pass


class EventStreamError(OpencodeError):
    """Raised when an event stream operation fails."""

    pass


class RetryExhaustedError(OpencodeError):
    """Raised when all retry attempts have been exhausted."""

    pass
