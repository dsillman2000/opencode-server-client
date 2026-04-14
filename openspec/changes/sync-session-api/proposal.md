## Why

With the HTTP foundation in place, we need to build core session management operations. Users must be able to create, list, get, delete, and track the status of sessions. This layer bridges the low-level HTTP client with domain-specific session logic, providing a clean sync API for session lifecycle management.

## What Changes

- **Session CRUD operations**: Create, read, list, delete sessions with clean sync API
- **Session status polling**: Retrieve and monitor session status (idle/busy/retry)
- **Session details**: Access session metadata including directory, title, parent relationship
- **Main client interface**: High-level `OpencodeServerClient` class that aggregates session operations
- **Prompt submission**: POST prompts to sessions with optional abort-before-submit
- **Response tracking**: Fetch messages and poll until session reaches idle state
- **Convenience methods**: `submit_and_wait()` pattern combining common workflows

## Capabilities

### New Capabilities

- `session-crud-sync`: Create, list, get, delete sessions (synchronous)
- `session-status-sync`: Poll and monitor session status (synchronous)
- `prompt-submission-sync`: Submit prompts with abort flag support (synchronous)
- `response-tracking-sync`: Fetch messages and poll for completion (synchronous)
- `opencode-client-sync`: Main synchronous client interface combining all operations

### Modified Capabilities

(None - this layer doesn't modify Layer 1 functionality)

## Impact

- **Code affected**: New module `src/opencode_server_client/session/` with sync implementation
- **APIs**: New public API classes: `SessionManager`, `PromptSubmitter`, `ResponsePoller`, `OpencodeServerClient`
- **Dependencies**: Builds on Layer 1 (http_client, config, types, exceptions)
- **Breaking changes**: None
- **Future impact**: Layer 3 (async API) will mirror these classes with async/await
