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

**Provider Management (Layer 1):**
- `ProviderManager`: Query available providers and their models with capabilities

**Session Management (Layer 2):**
- `OpencodeServerClient`: Main synchronous client with provider, session, and event management
- `SessionManager`: CRUD operations for sessions
- `PromptSubmitter`: Submit prompts and manage session abortion
- `EventSubscriber`: Subscribe to real-time events via SSE (background thread)

**Provider & Model Types:**
- `Provider`: Provider information with available models
- `Model`: Individual model with capabilities and pricing
- `ModelCapabilities`: Capabilities like text I/O, tool calls, reasoning
- `InputCapabilities` / `OutputCapabilities`: Specific I/O capabilities
- `ModelCost`: Pricing information for input/output

**Event Types:**
- `SessionStatusEvent`: Session status changed
- `SessionIdleEvent`: Session became idle
- `MessageUpdatedEvent`: Message content updated
- `MessagePartUpdatedEvent`: Partial message update (streaming)
- `SessionUpdatedEvent`: Session metadata updated
- `MessagePartDeltaEvent`: Incremental message part update
- `SessionErrorEvent`: Error in session
- `ServerHeartbeatEvent`: Server heartbeat (connection keep-alive)
- `SessionDiffEvent`: Session state diff/changes

**Type Definitions:**
- Core data models for sessions, messages, events, and worktrees

**Retry Behavior:**
All HTTP clients automatically retry on transient failures:
- 502 Bad Gateway
- 503 Service Unavailable
- Transport errors (connection errors, timeouts)

Non-retryable errors (4xx except timeout-related, 5xx except 502/503) are returned immediately.

Example:
    >>> from opencode_server_client import OpencodeServerClient, ServerConfig
    >>> config = ServerConfig(base_url="http://localhost:8000")
    >>> with OpencodeServerClient(config, default_directory="/path") as client:
    ...     # Query available providers and models
    ...     deepseek = client.providers.get_provider("deepseek")
    ...     model = deepseek.get_model("deepseek-chat")
    ...     if model.capabilities.has_text_io():
    ...         # Create a session and submit a prompt
    ...         session = client.create_session(title="My Session")
    ...         messages = client.submit_prompt_and_wait(
    ...             session_id=session["session_id"],
    ...             text="What's in this directory?",
    ...             provider_id="deepseek",
    ...             model_id="deepseek-chat"
    ...         )
    ...         for msg in messages:
    ...             print(msg)
"""

from opencode_server_client.client_sync import OpencodeServerClient
from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.events import (
    AnyEvent,
    EventParser,
    EventSubscriber,
    MessagePartDeltaEvent,
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    ServerHeartbeatEvent,
    SessionDiffEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionStatus,
    SessionStatusEvent,
    SessionUpdatedEvent,
)
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
from opencode_server_client.prompt import PromptSubmitter
from opencode_server_client.provider import ProviderManager
from opencode_server_client.provider.types import (
    InputCapabilities,
    Model,
    ModelCapabilities,
    ModelCost,
    OutputCapabilities,
    Provider,
    ProviderList,
)
from opencode_server_client.session import SessionManager
from opencode_server_client.types import (
    AssistantMessage,
    SessionMetadata,
    UserMessage,
    WorktreeMetadata,
)

__version__ = "0.1.0"

__all__ = [
    # Main Client
    "OpencodeServerClient",
    # Managers
    "ProviderManager",
    "SessionManager",
    "PromptSubmitter",
    "EventSubscriber",
    # Provider Types
    "Provider",
    "ProviderList",
    "Model",
    "ModelCapabilities",
    "ModelCost",
    "InputCapabilities",
    "OutputCapabilities",
    # Events
    "EventParser",
    "SessionStatusEvent",
    "SessionIdleEvent",
    "MessageUpdatedEvent",
    "MessagePartUpdatedEvent",
    "SessionUpdatedEvent",
    "MessagePartDeltaEvent",
    "SessionErrorEvent",
    "ServerHeartbeatEvent",
    "SessionDiffEvent",
    "SessionStatus",
    "AnyEvent",
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
