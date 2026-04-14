## Context

Layer 1 provides reliable HTTP communication with automatic retry. Now we need to build session management on top of it. The OpenCode server exposes session endpoints at `/session` (CRUD), `/session/{id}` (get/update), `/session/status` (status check), and `/session/{id}/prompt_async` (prompt submission). This layer encapsulates these patterns into easy-to-use classes.

## Goals / Non-Goals

**Goals:**
- Provide clean, discoverable sync API for session management
- Support creating, listing, getting, and deleting sessions
- Enable status polling to track session progress (idle/busy/retry states)
- Support prompt submission with optional abort-before-submit
- Provide response tracking (fetch messages, poll until idle)
- Create high-level main client that combines all operations
- Enable convenient workflows like "submit and wait for response"

**Non-Goals:**
- Session sharing/unsharing (Layer 5)
- Worktree management (separate manager)
- Event streaming (Layer 4)
- Async/await variants (Layer 3)
- Child sessions / session hierarchy details (defer)

## Decisions

### Decision 1: Manager Pattern for Organization

**Choice:** Create separate manager classes (`SessionManager`, `PromptSubmitter`, `ResponsePoller`) that are composed into main `OpencodeServerClient`

**Rationale:**
- Keeps concerns separated and discoverable
- Easier to test individual managers
- Allows users to access specific managers directly if needed
- Mirrors common UI library patterns (router, state, etc.)

**Alternatives Considered:**
- Single monolithic client: Too many methods; hard to discover
- Flat functions: Lose access to shared state and configuration

### Decision 2: Directory as Optional Everywhere

**Choice:** Accept `directory` as optional parameter on every operation; use client default if not provided

**Rationale:**
- Supports multi-project use cases
- Falls back to client-level default (reducing parameter noise)
- Matches OpenCode server API design

**Alternatives Considered:**
- Require directory always: Would complicate single-project use
- Only at client level: Would prevent per-operation override

### Decision 3: Status Polling with Timeout

**Choice:** `wait_for_idle()` method with configurable timeout and poll_interval; returns bool (success/timeout)

**Rationale:**
- Timeout prevents infinite waits
- Poll interval tradeoff between latency and load
- Returns bool for simple conditional logic
- Raised exceptions (SessionNotFound) for hard errors

**Alternatives Considered:**
- Raise TimeoutError: Less convenient for common case
- No timeout: Risky for long-running processes

### Decision 4: Abort Flag on Prompt Submission

**Choice:** `submit_prompt(..., abort=True)` parameter; if True, calls `/abort` before submitting

**Rationale:**
- User explicitly controls whether to abort
- Atomic operation (abort then submit in quick succession)
- Matches user intent: "abort and try again with new prompt"

**Alternatives Considered:**
- Separate `abort_then_submit()` method: More verbose
- Always abort: Destructive default

### Decision 5: Combined Submit+Wait Convenience Method

**Choice:** `OpencodeServerClient.submit_prompt_and_wait()` combines submit and polling

**Rationale:**
- Common workflow deserves ergonomic support
- Reduces boilerplate for typical use cases
- Still allows fine-grained control via separate methods

**Alternatives Considered:**
- Only expose low-level ops: Makes common case tedious

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Polling inefficiency**: Constant polling of /session/status could create load | Document poll_interval tuning; recommend SSE for high-frequency cases; start with 0.5s default |
| **Race conditions**: Session state may change between operations | Use SSE for real-time tracking (Layer 4); polling is eventual-consistency |
| **Directory context loss**: Forgetting to pass directory could operate on wrong project | Document in API; add verbose error messages; consider warnings in logging |
| **Long-running waits**: Timeout could be too short for complex prompts | Make timeout configurable; default to 5 minutes; document tuning |

## Migration Plan

This is the first sync session API; no migration needed. Async variant (Layer 3) will follow with parallel API.

## Open Questions

1. Should session creation validate that directory exists before creating session?
2. Should we cache session status locally or always fetch fresh?
3. What's the recommended timeout for typical prompts? (5 min? 10 min?)
4. Should we add session "reload" method to refresh metadata without polling?
