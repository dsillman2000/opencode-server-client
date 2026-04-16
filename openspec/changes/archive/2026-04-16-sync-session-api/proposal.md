## Why

With the HTTP foundation in place, we need to build core session management operations backed by real-time Server-Sent Events (SSE). For concurrent/real-time use cases, polling creates unnecessary server load. This layer provides a clean, event-driven sync API for session lifecycle management, using SSE as the foundation for both sync and async interfaces. The user-friendly client SDK abstracts away the SSE implementation details, providing a seamless experience whether users subscribe to events directly or use convenience methods.

## What Changes

- **Session CRUD operations**: Create, read, list, delete sessions with clean sync API
- **Event-driven session tracking**: Subscribe to real-time session status changes via SSE (idle/busy/error states)
- **Session details**: Access session metadata including directory, title, parent relationship
- **Main client interface**: High-level `OpencodeServerClient` class that aggregates session and event operations
- **Prompt submission**: POST prompts to sessions with optional abort-before-submit
- **Real-time response tracking**: Subscribe to message updates via SSE events
- **Convenience methods**: `submit_and_wait()` pattern combining submission and event subscription
- **Event subscription API**: Direct access to SSE event stream for advanced concurrent workflows

## Capabilities

### New Capabilities

- `session-crud-sync`: Create, list, get, delete sessions (synchronous)
- `event-subscription-sync`: Subscribe to real-time events via SSE (background thread-based, synchronous)
- `prompt-submission-sync`: Submit prompts with abort flag support (synchronous)
- `response-tracking-sync`: Subscribe to message updates and track session completion via events (synchronous)
- `opencode-client-sync`: Main synchronous client interface combining all operations
- `event-parsing`: Parse raw SSE events into typed Python objects for both sync and async contexts

### Modified Capabilities

(None - this layer doesn't modify Layer 1 functionality)

## Impact

- **Code affected**: New modules `src/opencode_server_client/session/`, `src/opencode_server_client/events/` with sync implementation
- **APIs**: New public API classes: `SessionManager`, `PromptSubmitter`, `EventSubscriber`, `OpencodeServerClient`, event type classes
- **Dependencies**: Builds on Layer 1 (http_client, config, types, exceptions); adds threading for sync event handling
- **Breaking changes**: None
- **Future impact**: Layer 3 (async API) will mirror these classes with async/await, reusing shared event parsing logic
