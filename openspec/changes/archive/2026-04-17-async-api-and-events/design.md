## Context

Layer 2 delivers event-driven session management via sync API with background threading. Layer 3 mirrors this with async/await, providing high-concurrency applications with a native async experience. Both layers use the same SSE foundation (`/global/event`) and reuse shared event types and parsing logic. This layer focuses on async equivalents and asyncio integration, not on adding new event capabilities.

## Goals / Non-Goals

**Goals:**
- Provide complete async/await API mirroring sync surface
- Support AsyncOpencodeServerClient as primary async entry point
- Enable efficient real-time updates via SSE event subscription (asyncio-based)
- Reuse event types and parser from Layer 2
- Support both callback and async iterator patterns for events
- Allow users to choose reactive (event-driven) or polling patterns if needed
- Maintain consistency with sync API surface

**Non-Goals:**
- Polling as primary mechanism (SSE is primary for both)
- Mixing sync and async in single client (use appropriate client)
- Server-side caching or local state management (keep stateless)
- Custom event filters/transforms (provide raw events + typed helpers)
- Worktree event handling (Layer 4+)

## Decisions

### Decision 1: Full Async Mirror vs. Wrapper

**Choice:** Implement separate AsyncSessionManager, AsyncPromptSubmitter, AsyncEventSubscriber classes (mirror not wrapper)

**Rationale:**
- Async has different patterns (coroutines, cancellation tokens, etc.)
- Wrapper-based approach would require complex abstractions
- Users never mix sync/async in same application
- Clear, understandable code for each mode
- Reuse shared event types (no duplication)

**Alternatives Considered:**
- Wrapper around sync: Defeats purpose of async (still blocking)
- Runtime switching: Confusing API surface

### Decision 2: Event-Driven Async, Not Polling

**Choice:** AsyncEventSubscriber uses asyncio tasks to read SSE stream; same /global/event as sync

**Rationale:**
- Consistent with Layer 2 (both event-driven)
- SSE is perfect for asyncio (stream of events maps to async iterator)
- No polling overhead; concurrency via asyncio, not threads
- Scales naturally to hundreds of concurrent sessions

**Alternatives Considered:**
- Async polling: Defeats purpose of async
- Only blocking operations: Loses concurrency benefits

### Decision 3: Callbacks + Async Iterator Support

**Choice:** AsyncEventSubscriber supports both callback-based subscriptions and async iterator pattern

**Rationale:**
- Callbacks match sync API surface for consistency
- Async iterator is more Pythonic for some workflows
- Users can choose pattern that fits their use case
- Easy to implement both; they're not mutually exclusive

**Alternatives Considered:**
- Callbacks only: Less Pythonic for async
- Async iterator only: Limits to one consumer; breaks parity with sync
- Neither: Makes event streaming awkward

### Decision 4: Shared Event Types Across Sync/Async

**Choice:** Reuse event types, parser from Layer 2; no async-specific variants

**Rationale:**
- Avoids code duplication
- Makes it easy to migrate from sync to async (same event model)
- EventParser is stateless; works for both contexts
- Reduces cognitive load: one event model, not sync and async variants

**Alternatives Considered:**
- Async-specific event types: Wastes code; confusing for users

### Decision 5: Error Handling in Async Event Streams

**Choice:** Pass errors to error_handler callback; stream continues on recoverable errors, stops on fatal

**Rationale:**
- Stream disruption should be explicit
- Allows user to log, retry, or gracefully degrade
- Fatal errors (auth, connection refused) stop stream
- Transient errors retried by HTTP client

**Alternatives Considered:**
- Raise exceptions: Would stop stream abruptly
- Silently ignore all errors: Lose visibility
- Retry forever: Could hang indefinitely

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Code duplication**: Async mirrors double async code | Good; keeps code clear and maintainable. Document shared patterns in design guide. |
| **Event callback latency**: User callbacks could block event processing in asyncio | Document that async callbacks should not block; use `asyncio.create_task()` for long operations |
| **SSE connection loss**: Network disruption could break stream | HTTP client retries transient errors; fatal errors trigger error_handler callback |
| **Event order guarantees**: SSE may reorder or lose events | Document eventual-consistency model; events are notifications, not transactions |
| **Backward compat**: Adding capabilities later without breaking | Events are stable; shared types reduce future churn |

## Migration Plan

No migration needed; this is additive API. Users choose sync or async based on their application architecture. Both are event-driven from the ground up.

## Open Questions

1. Should AsyncEventSubscriber.subscribe() accept both async callbacks and sync callbacks?
2. Should we provide an async context manager for automatic subscription cleanup?
3. What's the recommended pattern for collecting events in async workflows?
4. Should we buffer events and provide replay, or just stream live?

