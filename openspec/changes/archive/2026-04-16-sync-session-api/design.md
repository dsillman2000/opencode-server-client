## Context

Layer 1 provides reliable HTTP communication with automatic retry. Now we need to build session management on top of it backed by real-time events. The OpenCode server exposes SSE at `/global/event` for real-time updates and session endpoints at `/session` (CRUD), `/session/{id}` (get/update). This layer encapsulates SSE event subscription patterns and session operations into easy-to-use classes, supporting concurrent/real-time workflows without polling overhead.

## Goals / Non-Goals

**Goals:**
- Provide clean, discoverable sync API for session management
- Support creating, listing, getting, and deleting sessions
- Enable event-driven status tracking via SSE (no polling)
- Support prompt submission with optional abort-before-submit
- Provide real-time response tracking via SSE message events
- Enable event subscription for advanced concurrent workflows
- Create high-level main client that combines session and event operations
- Enable convenient workflows like "submit and wait for response" via events
- Abstract away threading complexity for sync users while providing raw event access for power users

**Non-Goals:**
- Session sharing/unsharing (Layer 5)
- Worktree management (separate manager)
- Async/await variants (Layer 3)
- Child sessions / session hierarchy details (defer)
- Local caching or state management (stateless event relay)

## Decisions

### Decision 1: Manager Pattern for Organization

**Choice:** Create separate manager classes (`SessionManager`, `PromptSubmitter`, `EventSubscriber`) that are composed into main `OpencodeServerClient`

**Rationale:**
- Keeps concerns separated and discoverable
- Easier to test individual managers
- Allows users to access specific managers directly if needed
- Mirrors common UI library patterns (router, state, etc.)
- SessionManager handles CRUD; EventSubscriber handles SSE; they're orthogonal concerns

**Alternatives Considered:**
- Single monolithic client: Too many methods; hard to discover
- Flat functions: Lose access to shared state and configuration

### Decision 2: SSE as Primary Event Source

**Choice:** Use `/global/event` SSE stream as primary mechanism for tracking session status and messages; no polling fallback

**Rationale:**
- Concurrent/real-time is the primary use case
- SSE eliminates unnecessary server load from polling
- Real-time updates enable responsive user interfaces
- Layer 1 HTTP client retries transient SSE errors automatically
- Foundation for both sync and async APIs

**Alternatives Considered:**
- Polling with optional SSE: Adds complexity; two code paths
- Only polling: Doesn't meet concurrency goals; creates server load

### Decision 3: Background Thread for Sync Event Handling

**Choice:** EventSubscriber uses background thread to read SSE; callbacks invoked in thread context

**Rationale:**
- Sync code doesn't have asyncio event loop running
- Thread-based approach allows sync code to remain blocking
- Callbacks can be simple functions; no async/await required
- Users can still write sync code naturally

**Alternatives Considered:**
- AsyncIO.run() for sync context: Pollutes global event loop; fragile
- Blocking HTTP calls only: Can't support concurrent subscriptions
- No threading: Can't provide event-driven experience in sync

### Decision 4: Directory as Optional Everywhere

**Choice:** Accept `directory` as optional parameter on every operation; use client default if not provided

**Rationale:**
- Supports multi-project use cases
- Falls back to client-level default (reducing parameter noise)
- Matches OpenCode server API design

**Alternatives Considered:**
- Require directory always: Would complicate single-project use
- Only at client level: Would prevent per-operation override

### Decision 5: Event-Driven Wait Pattern

**Choice:** `submit_and_wait()` internally subscribes to events; doesn't expose raw polling loops

**Rationale:**
- Simpler API for common use case
- Users don't need to understand threading/subscription mechanics
- Still allows power users to subscribe directly for fine-grained control

**Alternatives Considered:**
- Only expose low-level subscriptions: Requires users to write threading code
- Only high-level convenience method: Loses flexibility for concurrent workflows

### Decision 6: Shared Event Types Across Sync/Async

**Choice:** Define event types (SessionStatusEvent, MessageUpdatedEvent, etc.) in shared module; both sync and async use same types

**Rationale:**
- Avoids code duplication
- Makes it easy to migrate from sync to async (same event types)
- EventParser can be used by both sync and async layers
- Reduces cognitive load: one event model, not sync and async variants

**Alternatives Considered:**
- Separate event types per sync/async: Wastes code; confusing for users
- Sync uses dicts, async uses types: Inconsistent experience

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Threading complexity**: Background thread may confuse sync users | Document thread safety; provide `submit_and_wait()` convenience method; warn about callback context in docstrings |
| **SSE connection loss**: Network disruption could break stream | HTTP client retries transient errors; fatal errors trigger error_handler callback; user can reconnect |
| **Event order guarantees**: SSE may reorder or lose events | Document eventual-consistency model; events are notifications, not transactions |
| **GIL contention**: Callback code running in thread could slow down main thread | Document that callbacks should be quick; provide async event subscriber for compute-heavy workflows |
| **Subscription overhead**: Many concurrent subscriptions could create load | One SSE stream per client can multiplex many sessions; document recommended subscription patterns |

## Migration Plan

This is the first sync session API backed by events; no migration needed. Sync users will choose between raw subscription API (for concurrent workflows) or convenience methods (for simple blocking workflows).

## Open Questions

1. What is the exact schema of events from `/global/event`? (session.status, message.updated, etc.)
2. Should EventSubscriber support filtering by session_id at subscription time, or always receive all events?
3. What's the recommended error_handler behavior - should it log, raise, or just count?
4. Should session.get() fetch fresh metadata, or can it return cached data from events?
5. Should we buffer events during reconnection, or just stream live?

