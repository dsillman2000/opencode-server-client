"""OpenCode Server Client Library.

This package provides synchronous and asynchronous HTTP clients for
communicating with OpenCode servers, with built-in retry logic and
exponential backoff for transient failures.

**HTTP Clients:**
- `SyncHttpClient`: Synchronous HTTP client with automatic exponential backoff retry logic
- `AsyncHttpClient`: Asynchronous HTTP client with automatic exponential backoff retry logic

**Configuration:**
- `ServerConfig`: Configuration for OpenCode server connection (base_url, auth, timeout)
- `RetryConfig`: Configuration for exponential backoff retry behavior (max_retries, delays, base)

**Type Definitions:**
- Core data models for sessions, messages, events, and worktrees
- Event types for session status, messages, and errors

**Retry Behavior:**
All HTTP clients automatically retry on transient failures:
- 502 Bad Gateway
- 503 Service Unavailable
- Transport errors (connection errors, timeouts)

Non-retryable errors (4xx except timeout-related, 5xx except 502/503) are returned immediately.

Example:
    >>> from src.opencode_server_client import SyncHttpClient, ServerConfig, RetryConfig
    >>> config = ServerConfig(base_url="http://localhost:8000")
    >>> retry = RetryConfig(max_retries=3)
    >>> with SyncHttpClient(config, retry) as client:
    ...     response = client.get("/api/sessions")
    ...     print(response.status_code)
"""

from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.exceptions import (
    EventStreamError,
    OpencodeError,
    PromptSubmissionError,
    RetryExhaustedError,
    SessionCreationError,
    SessionError,
    SessionNotFoundError,
    WorktreeError,
)
from opencode_server_client.http_client import AsyncHttpClient, SyncHttpClient
from opencode_server_client.types import (
    AssistantMessage,
    MessageUpdatedEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionMetadata,
    SessionStatus,
    SessionStatusEvent,
    UserMessage,
    WorktreeMetadata,
)

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "ServerConfig",
    "RetryConfig",
    # HTTP Clients
    "SyncHttpClient",
    "AsyncHttpClient",
    # Type definitions
    "SessionMetadata",
    "UserMessage",
    "AssistantMessage",
    "WorktreeMetadata",
    "SessionStatus",
    "SessionStatusEvent",
    "SessionIdleEvent",
    "MessageUpdatedEvent",
    "SessionErrorEvent",
    # Exceptions
    "OpencodeError",
    "SessionError",
    "SessionCreationError",
    "SessionNotFoundError",
    "PromptSubmissionError",
    "WorktreeError",
    "EventStreamError",
    "RetryExhaustedError",
]
