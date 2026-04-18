## Why

Layer 2 provides a sync API backed by SSE for concurrent/real-time workflows. Modern Python applications also need async/await support for high-concurrency servers and applications. This layer mirrors all sync operations with async/await equivalents, reusing the shared event types and parser from Layer 2. Both sync and async APIs are event-driven from the ground up, providing a unified mental model whether users choose threading or asyncio.

## What Changes

- **Async session management**: Mirror all sync SessionManager operations with async/await
- **Async prompt operations**: Mirror PromptSubmitter with async/await
- **Async event subscription**: Event-driven SSE subscription using asyncio tasks (not polling)
- **Async main client**: AsyncOpencodeServerClient combining all async operations
- **Reused event infrastructure**: EventParser and event types shared with Layer 2 sync API
- **Async context managers**: Full support for `async with` patterns

## Capabilities

### New Capabilities

- `session-crud-async`: Async create, list, get, delete sessions (async/await)
- `prompt-submission-async`: Async prompt submission with abort support (async/await)
- `event-subscription-async`: Subscribe to SSE events asynchronously via asyncio tasks
- `opencode-client-async`: Main async client interface (async/await)

### Modified Capabilities

(None - this layer is additive; Layer 2 event infrastructure is reused)

## Impact

- **Code affected**: New modules `src/opencode_server_client/session/async_manager.py`, `src/opencode_server_client/events/async_subscriber.py`, etc.
- **APIs**: New public classes: AsyncSessionManager, AsyncPromptSubmitter, AsyncEventSubscriber, AsyncOpencodeServerClient
- **Dependencies**: Builds on Layer 2 (http_client, config, types, exceptions, shared events); uses httpx async support
- **Breaking changes**: None
- **Future impact**: Completes core event-driven API; enables Layer 4+ specialized features (worktrees, sharing, advanced state management)
