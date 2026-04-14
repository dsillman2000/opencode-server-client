## Context

Layer 2 delivered synchronous session management and polling. Modern Python applications need async/await support for concurrent operations, and polling-based status tracking creates unnecessary load on the server. The OpenCode server exposes SSE at `/global/event` for real-time updates. This layer mirrors all sync operations with async equivalents and adds event streaming for reactive workflows.

## Goals / Non-Goals

**Goals:**
- Provide complete async/await API mirroring sync surface
- Support AsyncOpencodeServerClient as primary async entry point
- Enable efficient real-time updates via SSE event subscription
- Parse raw SSE events into typed Python objects
- Support both sync (threading-based) and async (asyncio-based) event subscriptions
- Allow users to choose reactive (event-driven) or imperative (polling) patterns

**Non-Goals:**
- Mixing sync and async in single client (use appropriate client for your context)
- Server-side caching or local state management (keep stateless)
- Custom event filters/transforms (provide raw events + typed helpers)
- Worktree event handling (Layer 5)

## Decisions

### Decision 1: Full Async Mirror vs. Wrapper

**Choice:** Implement separate AsyncSessionManager, AsyncPromptSubmitter, AsyncResponsePoller classes (mirror not wrapper)

**Rationale:**
- Async has different patterns (coroutines, cancellation tokens, etc.)
- Wrapper-based approach would require complex abstractions
- Users never mix sync/async in same application
- Clear, understandable code for each mode

**Alternatives Considered:**
- Wrapper around sync: Defeats purpose of async (still blocking)
- Runtime switching: Confusing API surface

### Decision 2: SSE via Callbacks vs. Async Iterator

**Choice:** Callback-based subscriptions (both sync and async) with optional async iteration helper

**Rationale:**
- Matches common event patterns in Python (callbacks for reactive)
- Decouples event source from consumer
- Easy to implement filtering/routing in callbacks
- Supports multiple subscribers on same client

**Alternatives Considered:**
- Async iterator only: Limits to one consumer; less familiar pattern
- Polling only: Defeats purpose of SSE

### Decision 3: Background Thread vs. Task for Sync Events

**Choice:** Background thread for sync event subscription; asyncio task for async

**Rationale:**
- Sync code doesn't have asyncio event loop running
- Thread reads SSE stream; callback invoked in thread
- For async: asyncio task reads stream; callback awaited in task context
- Clean separation for each mode

**Alternatives Considered:**
- All via asyncio: Forces blocking sync code to use asyncio.run()
- All via threads: Inefficient for async applications

### Decision 4: Event Typing Strategy

**Choice:** Define typed event classes (SessionStatusEvent, MessageUpdatedEvent, etc.); parser maps raw SSE to types

**Rationale:**
- Type safety and IDE support
- Clear event schema via dataclasses
- Easy to pattern match on event types
- Can ignore unknown event types gracefully

**Alternatives Considered:**
- Dict[str, Any] throughout: Lose type checking
- Only TypeScript-like unions: No Python dataclass benefits

### Decision 5: Error Handling in Event Streams

**Choice:** Pass errors to error_handler callback; stream continues on recoverable errors, stops on fatal

**Rationale:**
- Stream disruption should be explicit
- Allows user to log, retry, or gracefully degrade
- Fatal errors (auth, connection refused) stop stream
- Transient errors (short network hiccup) retried by HTTP client

**Alternatives Considered:**
- Raise exceptions: Would stop stream abruptly
- Silently ignore all errors: Lose visibility
- Retry forever: Could hang indefinitely

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Code duplication**: Async mirrors double async code | Good; keeps code clear. Document shared patterns in design guide. |
| **Event callback complexity**: User callbacks could block event loop | Document that sync callbacks should be quick; async callbacks with await is safe |
| **SSE connection loss**: Network disruption could break stream | HTTP client retries transient errors; fatal errors trigger error_handler |
| **Event order guarantees**: SSE may reorder or lose events | Document eventual-consistency; events are hints, not transactions |
| **Backward compat**: Adding events later without breaking | Events are new; no compat concern for this layer |

## Migration Plan

No migration needed; this is additive API. Users choose sync or async based on their architecture.

## Open Questions

1. Should event subscriptions support filtering by session_id at subscription time?
2. Should we buffer events and provide replay, or just stream live?
3. What's the recommended error_handler behavior - should it log, raise, or just count?
4. Should we add event metrics/stats (events processed, errors, etc.)?
