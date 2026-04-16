# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-15

### Added

- **Sync Session API (Layer 2)**: Event-driven session management via Server-Sent Events (SSE)
  - `SessionManager`: CRUD operations for sessions (create, list, get, delete)
  - `PromptSubmitter`: Submit prompts and abort sessions with automatic UUID generation
  - `EventSubscriber`: Real-time SSE event subscription with background threading
  - `OpencodeServerClient`: Main high-level API combining all session and event operations
  
- **Event Infrastructure**: Unified event model for real-time updates
  - `SessionStatusEvent`: Tracks session state changes (idle, busy, retry)
  - `SessionIdleEvent`: Signals session readiness for input
  - `MessageUpdatedEvent`: Notifies when messages are modified
  - `MessagePartUpdatedEvent`: Streams individual message parts in real-time
  - `SessionErrorEvent`: Reports session-level errors with diagnostics
  - `EventParser`: Parses raw SSE streams into typed event objects with validation

- **Convenience Methods**:
  - `submit_prompt_and_wait()`: Submit a prompt and wait for completion with timeout support
  - Context manager support (`with` statement) for automatic resource cleanup
  - Optional directory context for directory-scoped operations via `X-Opencode-Directory` header

- **Features**:
  - Background threading for event subscription (non-blocking sync API)
  - Automatic reconnection with exponential backoff for robustness
  - Session ID filtering for efficient multiplexing of concurrent sessions
  - Thread-safe callback invocation with proper locking
  - Comprehensive docstrings with usage examples on all public APIs
  - Full type hints for IDE support and static type checking

- **Testing**: Extensive unit test coverage
  - 12 tests for `SessionManager` covering CRUD operations and error cases
  - 11 tests for `PromptSubmitter` covering submission variants and abort logic
  - 12 tests for `EventParser` covering all event types and error conditions
  - 13 tests for `EventSubscriber` covering threading, subscriptions, and filtering
  - 11 tests for `OpencodeServerClient` covering high-level API and context manager
  - Total: 60 new unit tests (>90% coverage of new code)

### Breaking Changes

- Session-related APIs are now SSE-backed (event-driven) rather than polling-based

## [0.1.0] - 2024-04-14

### Added

- **HTTP Client Foundation**: New synchronous and asynchronous HTTP clients for OpenCode server communication
  - `SyncHttpClient`: Synchronous HTTP client with automatic exponential backoff retry logic
  - `AsyncHttpClient`: Asynchronous HTTP client with automatic exponential backoff retry logic
  
- **Retry Logic**: Automatic retry mechanism with exponential backoff for transient failures
  - Retries on 502 Bad Gateway and 503 Service Unavailable HTTP responses
  - Retries on transport-level errors (connection failures, timeouts)
  - Non-retryable errors (4xx, 5xx except 502/503) are returned immediately
  - Configurable retry parameters: max_retries, initial_delay, max_delay, exponential_base

- **Configuration**: Configuration dataclasses for flexible client setup
  - `ServerConfig`: Base URL, basic auth, and timeout configuration
  - `RetryConfig`: Exponential backoff retry behavior configuration with validation

- **Type System**: Core type definitions for OpenCode server API
  - `SessionMetadata`: Session information and state
  - `UserMessage` and `AssistantMessage`: Message types for conversations
  - `WorktreeMetadata`: Project directory metadata
  - Event types: `SessionStatusEvent`, `SessionIdleEvent`, `MessageUpdatedEvent`, `SessionErrorEvent`
  - `SessionStatus`: Union type for session states (idle, busy, retry)

- **Exception Hierarchy**: Structured exception types for error handling
  - `OpencodeError`: Base exception class
  - `SessionError` and related: Session-specific exceptions
  - `RetryExhaustedError`: Raised when retry attempts are exhausted
  - Other domain exceptions: `PromptSubmissionError`, `WorktreeError`, `EventStreamError`

- **Features**:
  - Context manager support for both sync and async clients
  - `X-Opencode-Directory` header support for directory-scoped operations
  - Debug-level logging for retry attempts
  - Full type hints for IDE support and type checking
  - Comprehensive test coverage (89 tests, >90% coverage)

### Dependencies

- Requires: `httpx>=0.28.1` (already listed as dependency)
- Dev: Added `pytest-asyncio>=0.24.0` for async test support
