# SSE-First Architecture: Sync & Async Session APIs

## Overview

This document describes the consolidated architecture for Layers 2-3 of the OpenCode server client SDK. Both sync and async APIs are built on a **SSE-first, event-driven foundation**, eliminating polling and providing native support for concurrent/real-time workflows.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              User Application Code                          │
│                                                              │
│  Sync usage:          Async usage:                           │
│  client = OpencodeServerClient(...)                          │
│  messages = client.submit_prompt_and_wait(...)              │
│                                                              │
│  async_client = AsyncOpencodeServerClient(...)              │
│  messages = await async_client.submit_prompt_and_wait(...)  │
└──────────────┬──────────────────────────────────┬────────────┘
               │                                  │
        ┌──────▼──────────┐             ┌────────▼─────────┐
        │ Sync API Layer  │             │ Async API Layer  │
        │  (Layer 2)      │             │  (Layer 3)       │
        │                 │             │                  │
        │ OpencodeClient  │             │ AsyncOpencodeClient
        │ ├─ sessions     │             │ ├─ sessions
        │ ├─ prompts      │             │ ├─ prompts
        │ └─ events       │             │ └─ events
        └────────┬────────┘             └────────┬─────────┘
                 │ uses                         │ uses
        ┌────────▼──────────┐         ┌────────▼─────────┐
        │ EventSubscriber   │         │ AsyncEventSub    │
        │ (threading-based) │         │ (asyncio-based)  │
        └────────┬──────────┘         └────────┬─────────┘
                 │ both read                   │
                 │                             │
        ┌────────▼─────────────────────────────▼─────┐
        │  Shared SSE Infrastructure                 │
        │                                             │
        │  EventParser (raw SSE → typed events)      │
        │  Event types: SessionStatusEvent,          │
        │              MessageUpdatedEvent, etc.     │
        └────────┬──────────────────────────────────┘
                 │ reads
        ┌────────▼──────────────────────────┐
        │ HTTP Client with Retry (Layer 1)  │
        │ GET /global/event (SSE stream)    │
        │ POST /session/{id}/prompt_async   │
        │ POST /session/{id}/abort          │
        │ etc.                               │
        └────────┬──────────────────────────┘
                 │
        ┌────────▼──────────────────────────┐
        │ OpenCode Server                   │
        │ /global/event (SSE endpoint)      │
        │ /session/* (REST endpoints)       │
        └──────────────────────────────────┘
```

## Layer 2: Sync Session API (with SSE)

**Entry point:** `OpencodeServerClient`

**Core components:**

- `SessionManager`: CRUD operations (create, list, get, delete sessions)
- `PromptSubmitter`: Submit prompts, abort sessions
- `EventSubscriber`: Subscribe to real-time events via background thread
- Event types: Shared with Layer 3 (SessionStatusEvent, MessageUpdatedEvent, etc.)

**Threading model:**

- Main thread: Sync, blocking calls (create_session, etc.)
- Background thread: Reads SSE stream, invokes callbacks

**Common patterns:**

```python
# Simple case: submit and wait
messages = client.submit_prompt_and_wait(
    session_id=sid,
    text="hello",
    timeout=30
)

# Advanced case: subscribe to concurrent sessions
subscriber = client.events
messages = {}

def on_message(event):
    messages[event.session_id].append(event.content)

subscriber.subscribe(on_event=on_message)
client.prompts.submit(session_id1, text="hello")
client.prompts.submit(session_id2, text="help")
# Background thread receives events for both sessions
```

**Task count:** ~130 tasks (CRUD, events, tests, docs)

## Layer 3: Async Session API (with SSE)

**Entry point:** `AsyncOpencodeServerClient`

**Core components:**

- `AsyncSessionManager`: Async CRUD operations
- `AsyncPromptSubmitter`: Async prompt submission
- `AsyncEventSubscriber`: Subscribe via asyncio tasks
- Event types: **Reused from Layer 2** (no duplication)

**Concurrency model:**

- All I/O is async/await (no threads)
- Asyncio tasks for SSE stream reading
- Natural fit for high-concurrency servers

**Common patterns:**

```python
# Simple case: submit and wait
messages = await async_client.submit_prompt_and_wait(
    session_id=sid,
    text="hello",
    timeout=30
)

# Advanced case: concurrent sessions via asyncio
async def handle_session(sid, prompt):
    msgs = await async_client.submit_prompt_and_wait(sid, prompt)
    return msgs

results = await asyncio.gather(
    handle_session(sid1, "hello"),
    handle_session(sid2, "help"),
)

# Power-user case: async iterator over events
async for event in async_client.events:
    print(f"Received: {event}")
```

**Task count:** ~130 tasks (async equivalents, tests, docs, cross-layer consistency)

## Shared Infrastructure

### Event Type System

Defined once in `src/opencode_server_client/events/types.py`:

- `SessionStatusEvent` - Session state changes
- `SessionIdleEvent` - Session ready for input
- `MessageUpdatedEvent` - New/updated message
- `MessagePartUpdatedEvent` - Streaming response chunk
- `SessionErrorEvent` - Error occurred

All events include session_id, content, and timestamp.

### Event Parser

Defined once in `src/opencode_server_client/events/parser.py`:

- Converts raw SSE data to typed Python objects
- Used by both sync and async subscribers
- Handles unknown event types gracefully
- Validates event schema

### HTTP Client

Layer 1 (`SyncHttpClient` / `AsyncHttpClient`) handles:

- Connection pooling
- Retry logic (502, 503, transient errors)
- Basic auth, custom headers
- Both REST (POST /session, etc.) and SSE (GET /global/event)

## Key Architectural Decisions

### 1. SSE as Primary, No Polling

- `/global/event` is the foundation for both sync and async
- No polling for status; all updates via events
- Eliminates server load, enables concurrent/real-time workflows

### 2. Unified Event Model

- Both sync and async use identical event types
- EventParser is context-agnostic (works with both)
- Easy to migrate code from sync to async (just import different client)

### 3. Threading for Sync, Asyncio for Async

- **Sync:** Background thread reads SSE; callbacks in thread context
- **Async:** Asyncio task reads SSE; callbacks are coroutines
- Clean separation; no mixing

### 4. Convenience Methods Hide Complexity

- `submit_prompt_and_wait()` in both layers
- Hides event subscription details for common case
- Power users can access raw event subscriber directly

### 5. Directory as Optional Parameter

- Multi-project support: override per-call if needed
- Single-project simplicity: use client default
- Consistent with Layer 1 HTTP client

## Development Order

1. **Build shared event infrastructure first** (Layer 2 + Layer 3 Foundation)
   - Event types, parser (used by both)
   - Estimated: ~2 weeks

2. **Implement sync layer** (Layer 2)
   - SessionManager, PromptSubmitter (sync)
   - EventSubscriber (threading-based)
   - Main client, tests, docs
   - Estimated: ~3 weeks

3. **Implement async layer** (Layer 3)
   - AsyncSessionManager, AsyncPromptSubmitter (async)
   - AsyncEventSubscriber (asyncio-based)
   - Main client, tests, docs, cross-layer parity tests
   - Estimated: ~2.5 weeks (shorter because most logic is identical to sync)

## Migration Path: Polling to Events

Users still on polling (if we had implemented it) would migrate:

```python
# Old (polling, not implemented in this design)
# for _ in range(100):
#     if client.wait_for_idle(timeout=0.5):
#         break

# New (events)
messages = client.submit_prompt_and_wait(timeout=30)
```

Since we're SSE-first, there's no migration needed; polling never existed.

## Error Handling Strategy

### Transient Errors (retried by HTTP client)

- Network timeouts
- 502 Bad Gateway
- 503 Service Unavailable

### Recoverable Errors (trigger reconnection)

- SSE connection drops
- Short network hiccup
- Exponential backoff reconnection

### Fatal Errors (stop stream)

- 401 Unauthorized
- 403 Forbidden
- Connection refused

### Application Errors

- Invalid JSON in event
- Missing required fields
- Unknown event type

## Testing Strategy

### Layer 2 (Sync)

- Mock HTTP client for unit tests
- Thread safety tests (multiple callbacks)
- Background thread lifecycle tests
- Integration tests with real server (optional)

### Layer 3 (Async)

- Mock async HTTP client
- Asyncio task lifecycle tests
- Concurrent session handling tests
- Async/await pattern validation

### Cross-Layer

- Event type consistency (sync == async)
- API surface parity (same methods, different keywords)
- Shared event parser correctness

## Performance Characteristics

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Session creation | ~50ms | Limited by HTTP |
| Message arrival (via event) | <10ms | 1000+ events/sec per connection |
| Concurrent sessions | O(sessions) via SSE multiplex | 100+ sessions on single connection |
| Polling (if used) | 0.5s min | Limited to ~2 requests/sec per session |

## Security Considerations

- All traffic via authenticated HTTP/HTTPS
- SSE inherits auth from HTTP client (basic auth, headers)
- Per-session filtering: EventSubscriber can filter by session_id
- No sensitive data in event objects (references only)

## Future Enhancements

- Event replay/buffering for missed events
- Event filtering at subscription time (type, session_id)
- Metrics/stats on event processing
- Persistent event log (optional, server-side)
- Event compression for high-throughput scenarios
