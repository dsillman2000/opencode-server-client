## 1. Async Session Manager Implementation

- [x] 1.1 Create `src/opencode_server_client/session/async_manager.py`
- [x] 1.2 Implement `AsyncSessionManager` class with async HTTP client
- [x] 1.3 Implement `AsyncSessionManager.create()` - async POST /session
- [x] 1.4 Implement `AsyncSessionManager.list()` - async GET /session
- [x] 1.5 Implement `AsyncSessionManager.get()` - async GET /session/{id}
- [x] 1.6 Implement `AsyncSessionManager.delete()` - async DELETE /session/{id}

## 2. Async Prompt Submission Implementation

- [x] 2.1 Create `src/opencode_server_client/prompt/async_submitter.py`
- [x] 2.2 Implement `AsyncPromptSubmitter` class with async HTTP client
- [x] 2.3 Implement `AsyncPromptSubmitter.submit_prompt()` - async POST /session/{id}/prompt_async
- [x] 2.4 Support optional message_id generation (UUID) in async context
- [x] 2.5 Implement abort-before-submit logic in async `submit_prompt(abort=True)`
- [x] 2.6 Implement `AsyncPromptSubmitter.abort_session()` - async POST /session/{id}/abort

## 3. Async Event Subscription Implementation

- [x] 3.1 Create `src/opencode_server_client/events/async_subscriber.py`
- [x] 3.2 Implement `AsyncEventSubscriber` class for async SSE handling
- [x] 3.3 Implement asyncio task management for SSE stream (`_listen_task`, `_cancel_event`)
- [x] 3.4 Implement `subscribe(on_event=None, on_idle=None, on_error=None)` async callbacks
- [x] 3.5 Implement `_read_sse_stream()` coroutine - asyncio task reads `/global/event`
- [x] 3.6 Implement event parsing and async callback dispatch
- [x] 3.7 Implement async iterator support: `async for event in subscriber`
- [x] 3.8 Implement `unsubscribe()` - cancels asyncio task
- [x] 3.9 Implement `close()` - gracefully shutdown asyncio task
- [x] 3.10 Implement connection lifecycle: connect, listen, disconnect
- [x] 3.11 Handle SSE disconnections and automatic reconnection with exponential backoff
- [x] 3.12 Implement coroutine-safe callback invocation and error handling
- [x] 3.13 Implement filtering: `subscribe(session_id_filter=None)` to filter events

## 4. Async Main Client Implementation

- [x] 4.1 Create `src/opencode_server_client/client_async.py`
- [x] 4.2 Implement `AsyncOpencodeServerClient` class with async manager composition
- [x] 4.3 Implement async manager property accessors (sessions, prompts, events)
- [x] 4.4 Implement async convenience methods: `create_session()`, `list_all_sessions()`, `delete_session()`
- [x] 4.5 Implement `submit_prompt_and_wait()` async convenience combining submission and event subscription
- [x] 4.6 Implement async context manager support (`__aenter__`, `__aexit__`)
- [x] 4.7 Add logging and error handling throughout
- [x] 4.8 Add type hints to all public methods

## 5. Package Integration

- [x] 5.1 Update `src/opencode_server_client/__init__.py` to export async client classes
- [x] 5.2 Export AsyncSessionManager, AsyncPromptSubmitter, AsyncEventSubscriber, AsyncOpencodeServerClient
- [x] 5.3 Verify shared event types and parser are properly exported
- [x] 5.4 Verify no import cycles or circular dependencies
- [x] 5.5 Add comprehensive module-level docstrings

## 6. Unit Tests - Async Session Manager

- [x] 6.1 Create `tests/test_session_manager_async.py`
- [x] 6.2 Mock async HTTP client for all tests
- [x] 6.3 Test async create() with minimal params
- [x] 6.4 Test async create() with title and parent_id
- [x] 6.5 Test async create() with 400 error
- [x] 6.6 Test async list() returns session list
- [x] 6.7 Test async list() with empty directory
- [x] 6.8 Test async get() with valid session_id
- [x] 6.9 Test async get() with 404 error
- [x] 6.10 Test async delete() succeeds
- [x] 6.11 Test async delete() with 404 error
- [x] 6.12 Test default directory override

## 7. Unit Tests - Async Prompt Submitter

- [x] 7.1 Create `tests/test_prompt_submitter_async.py`
- [x] 7.2 Test async submit_prompt() with text only
- [x] 7.3 Test async submit_prompt() with agent parameter
- [x] 7.4 Test async submit_prompt() with system prompt
- [x] 7.5 Test async submit_prompt() with tools config
- [x] 7.6 Test async submit_prompt() auto-generates message_id
- [x] 7.7 Test async submit_prompt() with custom message_id
- [x] 7.8 Test async submit_prompt() with abort=False (no abort call)
- [x] 7.9 Test async submit_prompt() with abort=True (abort then submit)
- [x] 7.10 Test async abort_session() succeeds
- [x] 7.11 Test async abort_session() with 404 error

## 8. Unit Tests - Async Event Subscriber

- [x] 8.1 Create `tests/test_event_subscriber_async.py`
- [x] 8.2 Mock async SSE HTTP client for tests
- [x] 8.3 Test async subscribe() registers async callback
- [x] 8.4 Test unsubscribe() cancels asyncio task
- [x] 8.5 Test async callback invoked on message event
- [x] 8.6 Test on_idle async callback invoked when session idle
- [x] 8.7 Test on_error async callback invoked on error event
- [x] 8.8 Test multiple async callbacks can subscribe simultaneously
- [x] 8.9 Test asyncio task starts on first subscribe
- [x] 8.10 Test async callback invocation (coroutine execution)
- [x] 8.11 Test close() stops asyncio task gracefully
- [x] 8.12 Test reconnection with exponential backoff on connection error
- [x] 8.13 Test async callback errors don't crash listener task
- [x] 8.14 Test session_id filtering: only matching events trigger callbacks
- [x] 8.15 Test async iterator pattern: `async for event in subscriber`
- [x] 8.16 Test SSE stream parsing with multiple events

## 9. Unit Tests - Async Main Client

- [x] 9.1 Create `tests/test_opencode_client_async.py`
- [x] 9.2 Test async client initialization with defaults
- [x] 9.3 Test async client initialization with all parameters
- [x] 9.4 Test async manager property accessors (sessions, prompts, events)
- [x] 9.5 Test async convenience methods (create_session, list_all_sessions, delete_session)
- [x] 9.6 Test async submit_prompt_and_wait() succeeds
- [x] 9.7 Test async submit_prompt_and_wait() times out (on_idle not called)
- [x] 9.8 Test async submit_prompt_and_wait() with abort=True
- [x] 9.9 Test async submit_prompt_and_wait() collects messages from callbacks
- [x] 9.10 Test async context manager support (`async with`)
- [x] 9.11 Test cleanup on context manager exit

## 10. Integration Tests - Async

- [x] 10.1 Create `tests/integration_async.py` for async end-to-end workflows
- [x] 10.2 Test complete async workflow: create → subscribe → submit → wait for idle
- [x] 10.3 Test receive multiple message events before idle
- [x] 10.4 Test async abort and resubmit workflow with events
- [x] 10.5 Test timeout handling in realistic scenarios
- [x] 10.6 Test error event handling during session
- [x] 10.7 Test concurrent subscriptions (multiple sessions with asyncio)
- [x] 10.8 Test SSE reconnection on network hiccup
- [x] 10.9 Test retry logic integration with HTTP client (502 scenario)
- [x] 10.10 Test mixing multiple concurrent async clients

## 11. Integration Tests - Cross-Layer Consistency

- [x] 11.1 Create `tests/integration_sync_async_parity.py`
- [x] 11.2 Test sync and async event types are identical
- [x] 11.3 Test sync and async clients have parallel APIs
- [x] 11.4 Test shared event parser works with both sync and async
- [x] 11.5 Test event data structure consistency between layers

## 12. Documentation & Finalization

- [x] 12.1 Add comprehensive docstrings to all async public methods
- [x] 12.2 Document async/await patterns in module docstrings
- [x] 12.3 Document asyncio task lifecycle and cancellation
- [x] 12.4 Add type hints to all async parameters and returns
- [x] 12.5 Run type checker (mypy/pyright) for async code
- [x] 12.6 Verify all async tests pass with >90% coverage
- [x] 12.7 Add async context manager usage examples to docstrings
- [x] 12.8 Document async iterator pattern for event consumption
- [x] 12.9 Update CHANGELOG with async/event features
- [x] 12.10 Create migration guide: "Sync to Async" (how to port code)
- [x] 12.11 Review for consistency with Layer 2 conventions
- [x] 12.12 Document reconnection behavior and backoff strategy
- [x] 12.13 Add usage examples in docstrings (concurrent workflows, streaming)
