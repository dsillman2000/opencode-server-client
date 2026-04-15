## Context

The OpenCode server exposes a REST API that clients must call to manage sessions, submit prompts, and track state. Current implementations (legacy mlflow_opencode) use ad-hoc httpx client setup with basic retry logic. This layer needs to be formalized into a reusable, configurable foundation supporting both sync and async usage patterns with exponential backoff resilience.

## Goals / Non-Goals

**Goals:**
- Provide sync and async HTTP clients with automatic exponential backoff retry logic
- Support transient failure recovery (502/503, transport errors) without user code
- Enable configuration of retry parameters per-client
- Establish type definitions for core domain objects (sessions, messages, events, worktrees)
- Create reusable foundation that higher layers (sessions, prompts, events) depend on

**Non-Goals:**
- Event streaming (handled in later layer)
- Session management logic (handled in later layer)
- Prompt submission/response tracking (handled in later layer)
- Authentication beyond basic auth (future enhancement)
- Request rate limiting or quota management

## Decisions

### Decision 1: Separate Sync and Async Implementations

**Choice:** Duplicate async equivalents alongside sync code (AsyncHttpClient alongside SyncHttpClient)

**Rationale:** 
- Sync and async have fundamentally different patterns (threading vs. asyncio)
- Shared code would require complex abstraction that obscures clarity
- Users choose one model or the other per-application; they don't mix them in one client
- Clearer code and API surface

**Alternatives Considered:**
- Single client with runtime switching: Violates "one way to do it" principle; confusing API
- Async-only with sync wrapper: asyncio.run() wrapper is inefficient for long-lived programs
- Generator-based abstraction: Overly complex for HTTP operations

### Decision 2: Exponential Backoff Configuration

**Choice:** Per-client configuration via `RetryConfig` dataclass with: max_retries, initial_delay, max_delay, exponential_base

**Rationale:**
- Different clients may need different retry policies (batch vs. interactive)
- Exponential backoff prevents server overload during outages
- Capping max_delay prevents excessive waits (typically 30s is enough)
- Formula: `delay = min(initial_delay * (base ^ attempt), max_delay)`

**Alternatives Considered:**
- No configuration (fixed policy): Inflexible for different use cases
- Per-method override: Adds complexity; client-level config is sufficient
- Jitter: Deferred to v2 (can add without API change)

### Decision 3: Retryable Status Codes

**Choice:** Auto-retry on 502, 503, and TransportError. No retry on 4xx, 401, 5xx except 502/503.

**Rationale:**
- 502/503 indicate temporary gateway/service unavailability
- TransportError suggests network hiccup (connection reset, timeout during request)
- 4xx are client errors (invalid request) - retrying won't help
- 401 is auth failure - retrying won't help
- Other 5xx (500, 504) are server errors that *might* benefit from retry, but 502/503 are the clearest transient cases

**Alternatives Considered:**
- Retry all 5xx: Too broad; includes permanent errors
- Custom retryable status set: Can add in v2 as option

### Decision 4: Directory Context via Header

**Choice:** Accept optional `directory` parameter in operations; pass via `X-Opencode-Directory` header

**Rationale:**
- Server API expects directory context for multi-project support
- Header approach keeps URL clean and integrates with middleware
- Matches existing legacy implementation

**Alternatives Considered:**
- Path parameter: Would require API wrapper
- Query parameter: Less RESTful; easily lost in redirects

### Decision 5: Type System Structure

**Choice:** Define type classes at Layer 2, organize by domain (SessionMetadata, Message, SessionStatus, etc.)

**Rationale:**
- Clear separation of concerns
- Enables type checking and IDE support
- API references (.sdk.js) already define event/message schemas; we extract those into Python types

**Alternatives Considered:**
- Dict[str, Any] throughout: No type safety; error-prone
- Pydantic models: Adds dependency; dataclasses sufficient for now

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Async complexity**: Dual code paths doubles maintenance burden | Document both clearly; share test patterns; add integration tests |
| **Backoff storms**: Multiple clients backing off simultaneously could still hammer server | Recommend jitter in docs (v2 feature); start with conservative defaults |
| **Header loss in redirects**: `X-Opencode-Directory` may be lost in redirects | Server should handle in redirects; document expectation |
| **Type coupling**: Python types must stay in sync with server API schema | Auto-generate from api.sdk.js periodically; document in contribution guide |

## Migration Plan

This is a new foundation layer; no migration needed. Subsequent layers (Layer 3+) will be built atop this.

## Open Questions

1. Should we auto-generate Python types from `api.sdk.js` to keep in sync, or maintain manually?
2. Should we add telemetry/logging for retry attempts (debug-level logging)?
3. Should connection pooling be managed at this layer or left to httpx defaults?
4. For async, should we support contextvars for directory context (thread-local equivalent)?
