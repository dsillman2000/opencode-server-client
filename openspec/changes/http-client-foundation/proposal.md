## Why

The `opencode-server-client` library needs a solid HTTP foundation to reliably communicate with OpenCode servers. Current approach lacks automatic retry logic and exponential backoff for transient failures. A robust, configurable HTTP client with built-in resilience is essential before higher-level session and prompt APIs can be built reliably.

## What Changes

- **New HTTP abstraction layer** with both synchronous and asynchronous implementations
- **Automatic exponential backoff retry logic** for transient failures (502/503 errors, transport errors)
- **Configurable retry parameters** (max retries, initial delay, max delay, base multiplier)
- **Context-aware headers** including `X-Opencode-Directory` for directory scoping
- **Type system foundation** with core data models (SessionMetadata, Message types, SessionStatus, WorktreeMetadata)
- **Exception hierarchy** for structured error handling

## Capabilities

### New Capabilities

- `http-client-sync`: Synchronous HTTP client with retry/backoff for OpenCode API
- `http-client-async`: Asynchronous HTTP client with retry/backoff for OpenCode API
- `retry-configuration`: Configurable exponential backoff parameters for all HTTP operations
- `core-data-types`: Type definitions for sessions, messages, worktrees, and server events

### Modified Capabilities

(None - this is foundational)

## Impact

- **Code affected**: Will introduce new module `src/opencode_server_client/http_client/` 
- **APIs**: No public API changes yet; this is internal infrastructure
- **Dependencies**: Adds `httpx` as core dependency (already required)
- **Breaking changes**: None
- **Future impact**: All Layer 2+ APIs (sessions, prompts, events) depend on this layer

