## 1. Async Session Manager Implementation

- [ ] 1.1 Create `src/opencode_server_client/session/async_manager.py`
- [ ] 1.2 Implement `AsyncSessionManager` class with async HTTP client
- [ ] 1.3 Implement `AsyncSessionManager.create()` - async POST /session
- [ ] 1.4 Implement `AsyncSessionManager.list()` - async GET /session
- [ ] 1.5 Implement `AsyncSessionManager.get()` - async GET /session/{id}
- [ ] 1.6 Implement `AsyncSessionManager.delete()` - async DELETE /session/{id}

## 2. Async Prompt Submission Implementation

- [ ] 2.1 Create `src/opencode_server_client/prompt/async_submitter.py`
- [ ] 2.2 Implement `AsyncPromptSubmitter` class with async HTTP client
- [ ] 2.3 Implement `AsyncPromptSubmitter.submit_prompt()` - async POST /session/{id}/prompt_async
- [ ] 2.4 Support optional message_id generation (UUID) in async context
- [ ] 2.5 Implement abort-before-submit logic in async `submit_prompt(abort=True)`
- [ ] 2.6 Implement `AsyncPromptSubmitter.abort_session()` - async POST /session/{id}/abort

## 3. Async Event Subscription Implementation

- [ ] 3.1 Create `src/opencode_server_client/events/async_subscriber.py`
- [ ] 3.2 Implement `AsyncEventSubscriber` class for async SSE handling
- [ ] 3.3 Implement asyncio task management for SSE stream (`_listen_task`, `_cancel_event`)
- [ ] 3.4 Implement `subscribe(on_event=None, on_idle=None, on_error=None)` async callbacks
- [ ] 3.5 Implement `_read_sse_stream()` coroutine - asyncio task reads `/global/event`
- [ ] 3.6 Implement event parsing and async callback dispatch
- [ ] 3.7 Implement async iterator support: `async for event in subscriber`
- [ ] 3.8 Implement `unsubscribe()` - cancels asyncio task
- [ ] 3.9 Implement `close()` - gracefully shutdown asyncio task
- [ ] 3.10 Implement connection lifecycle: connect, listen, disconnect
- [ ] 3.11 Handle SSE disconnections and automatic reconnection with exponential backoff
- [ ] 3.12 Implement coroutine-safe callback invocation and error handling
- [ ] 3.13 Implement filtering: `subscribe(session_id_filter=None)` to filter events

## 4. Async Main Client Implementation

- [ ] 4.1 Create `src/opencode_server_client/client_async.py`
- [ ] 4.2 Implement `AsyncOpencodeServerClient` class with async manager composition
- [ ] 4.3 Implement async manager property accessors (sessions, prompts, events)
- [ ] 4.4 Implement async convenience methods: `create_session()`, `list_all_sessions()`, `delete_session()`
- [ ] 4.5 Implement `submit_prompt_and_wait()` async convenience combining submission and event subscription
- [ ] 4.6 Implement async context manager support (`__aenter__`, `__aexit__`)
- [ ] 4.7 Add logging and error handling throughout
- [ ] 4.8 Add type hints to all public methods

## 5. Package Integration

- [ ] 5.1 Update `src/opencode_server_client/__init__.py` to export async client classes
- [ ] 5.2 Export AsyncSessionManager, AsyncPromptSubmitter, AsyncEventSubscriber, AsyncOpencodeServerClient
- [ ] 5.3 Verify shared event types and parser are properly exported
- [ ] 5.4 Verify no import cycles or circular dependencies
- [ ] 5.5 Add comprehensive module-level docstrings

## 6. Unit Tests - Async Session Manager

- [ ] 6.1 Create `tests/test_session_manager_async.py`
- [ ] 6.2 Mock async HTTP client for all tests
- [ ] 6.3 Test async create() with minimal params
- [ ] 6.4 Test async create() with title and parent_id
- [ ] 6.5 Test async create() with 400 error
- [ ] 6.6 Test async list() returns session list
- [ ] 6.7 Test async list() with empty directory
- [ ] 6.8 Test async get() with valid session_id
- [ ] 6.9 Test async get() with 404 error
- [ ] 6.10 Test async delete() succeeds
- [ ] 6.11 Test async delete() with 404 error
- [ ] 6.12 Test default directory override

## 7. Unit Tests - Async Prompt Submitter

- [ ] 7.1 Create `tests/test_prompt_submitter_async.py`
- [ ] 7.2 Test async submit_prompt() with text only
- [ ] 7.3 Test async submit_prompt() with agent parameter
- [ ] 7.4 Test async submit_prompt() with system prompt
- [ ] 7.5 Test async submit_prompt() with tools config
- [ ] 7.6 Test async submit_prompt() auto-generates message_id
- [ ] 7.7 Test async submit_prompt() with custom message_id
- [ ] 7.8 Test async submit_prompt() with abort=False (no abort call)
- [ ] 7.9 Test async submit_prompt() with abort=True (abort then submit)
- [ ] 7.10 Test async abort_session() succeeds
- [ ] 7.11 Test async abort_session() with 404 error

## 8. Unit Tests - Async Event Subscriber

- [ ] 8.1 Create `tests/test_event_subscriber_async.py`
- [ ] 8.2 Mock async SSE HTTP client for tests
- [ ] 8.3 Test async subscribe() registers async callback
- [ ] 8.4 Test unsubscribe() cancels asyncio task
- [ ] 8.5 Test async callback invoked on message event
- [ ] 8.6 Test on_idle async callback invoked when session idle
- [ ] 8.7 Test on_error async callback invoked on error event
- [ ] 8.8 Test multiple async callbacks can subscribe simultaneously
- [ ] 8.9 Test asyncio task starts on first subscribe
- [ ] 8.10 Test async callback invocation (coroutine execution)
- [ ] 8.11 Test close() stops asyncio task gracefully
- [ ] 8.12 Test reconnection with exponential backoff on connection error
- [ ] 8.13 Test async callback errors don't crash listener task
- [ ] 8.14 Test session_id filtering: only matching events trigger callbacks
- [ ] 8.15 Test async iterator pattern: `async for event in subscriber`
- [ ] 8.16 Test SSE stream parsing with multiple events

## 9. Unit Tests - Async Main Client

- [ ] 9.1 Create `tests/test_opencode_client_async.py`
- [ ] 9.2 Test async client initialization with defaults
- [ ] 9.3 Test async client initialization with all parameters
- [ ] 9.4 Test async manager property accessors (sessions, prompts, events)
- [ ] 9.5 Test async convenience methods (create_session, list_all_sessions, delete_session)
- [ ] 9.6 Test async submit_prompt_and_wait() succeeds
- [ ] 9.7 Test async submit_prompt_and_wait() times out (on_idle not called)
- [ ] 9.8 Test async submit_prompt_and_wait() with abort=True
- [ ] 9.9 Test async submit_prompt_and_wait() collects messages from callbacks
- [ ] 9.10 Test async context manager support (`async with`)
- [ ] 9.11 Test cleanup on context manager exit

## 10. Integration Tests - Async

- [ ] 10.1 Create `tests/integration_async.py` for async end-to-end workflows
- [ ] 10.2 Test complete async workflow: create → subscribe → submit → wait for idle
- [ ] 10.3 Test receive multiple message events before idle
- [ ] 10.4 Test async abort and resubmit workflow with events
- [ ] 10.5 Test timeout handling in realistic scenarios
- [ ] 10.6 Test error event handling during session
- [ ] 10.7 Test concurrent subscriptions (multiple sessions with asyncio)
- [ ] 10.8 Test SSE reconnection on network hiccup
- [ ] 10.9 Test retry logic integration with HTTP client (502 scenario)
- [ ] 10.10 Test mixing multiple concurrent async clients

## 11. Integration Tests - Cross-Layer Consistency

- [ ] 11.1 Create `tests/integration_sync_async_parity.py`
- [ ] 11.2 Test sync and async event types are identical
- [ ] 11.3 Test sync and async clients have parallel APIs
- [ ] 11.4 Test shared event parser works with both sync and async
- [ ] 11.5 Test event data structure consistency between layers

## 12. Documentation & Finalization

- [ ] 12.1 Add comprehensive docstrings to all async public methods
- [ ] 12.2 Document async/await patterns in module docstrings
- [ ] 12.3 Document asyncio task lifecycle and cancellation
- [ ] 12.4 Add type hints to all async parameters and returns
- [ ] 12.5 Run type checker (mypy/pyright) for async code
- [ ] 12.6 Verify all async tests pass with >90% coverage
- [ ] 12.7 Add async context manager usage examples to docstrings
- [ ] 12.8 Document async iterator pattern for event consumption
- [ ] 12.9 Update CHANGELOG with async/event features
- [ ] 12.10 Create migration guide: "Sync to Async" (how to port code)
- [ ] 12.11 Review for consistency with Layer 2 conventions
- [ ] 12.12 Document reconnection behavior and backoff strategy
- [ ] 12.13 Add usage examples in docstrings (concurrent workflows, streaming)
