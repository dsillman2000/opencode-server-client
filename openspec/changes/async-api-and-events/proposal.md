## Why

The synchronous API is complete, but modern Python applications increasingly use async/await for concurrency. Users need both patterns: sync for simple scripts and threads, async for high-concurrency servers and applications. Additionally, polling for session updates is inefficient; SSE (Server-Sent Events) provides real-time updates. This layer mirrors the sync API with async/await and adds event streaming for reactive workflows.

## What Changes

- **Async session management**: Mirror all sync SessionManager operations with async/await
- **Async prompt operations**: Mirror PromptSubmitter with async/await
- **Async response tracking**: Mirror ResponsePoller with async/await
- **Async main client**: AsyncOpencodeServerClient combining all async operations
- **SSE event streaming**: Subscribe to real-time events with typed callbacks
- **Event parsing**: Convert raw SSE events to typed Python objects (SessionStatusEvent, MessageUpdatedEvent, etc.)
- **Background event handling**: Thread-based (sync) and task-based (async) event subscriptions

## Capabilities

### New Capabilities

- `session-crud-async`: Async create, list, get, delete sessions (async/await)
- `prompt-submission-async`: Async prompt submission with abort support (async/await)
- `response-tracking-async`: Async message fetching and completion polling (async/await)
- `opencode-client-async`: Main async client interface (async/await)
- `event-subscription-sync`: Subscribe to SSE events synchronously (background thread)
- `event-subscription-async`: Subscribe to SSE events asynchronously (asyncio task)
- `event-parsing`: Parse raw SSE events to typed Python objects

### Modified Capabilities

(None - this layer is additive)

## Impact

- **Code affected**: New modules `src/opencode_server_client/session/async_manager.py`, etc.; new `events/` module
- **APIs**: New public classes: AsyncSessionManager, AsyncPromptSubmitter, AsyncResponsePoller, AsyncOpencodeServerClient, EventSubscriber, AsyncEventSubscriber, EventParser
- **Dependencies**: Adds `aiohttp` or keeps httpx for async (already has asyncio support)
- **Breaking changes**: None
- **Future impact**: Completes core API; enables Layer 5+ specialized features (worktrees, sharing, advanced state management)
