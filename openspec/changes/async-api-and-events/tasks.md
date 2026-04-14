## 1. Async Session Manager Implementation

- [ ] 1.1 Create `src/opencode_server_client/session/async_manager.py`
- [ ] 1.2 Implement `AsyncSessionManager` class with async HTTP client
- [ ] 1.3 Implement `AsyncSessionManager.create()` - async POST /session
- [ ] 1.4 Implement `AsyncSessionManager.list()` - async GET /session
- [ ] 1.5 Implement `AsyncSessionManager.get()` - async GET /session/{id}
- [ ] 1.6 Implement `AsyncSessionManager.delete()` - async DELETE /session/{id}
- [ ] 1.7 Implement `AsyncSessionManager.get_status()` - async GET /session/status
- [ ] 1.8 Implement `AsyncSessionManager.wait_for_idle()` with async polling

## 2. Async Prompt Submission Implementation

- [ ] 2.1 Create `src/opencode_server_client/prompt/async_submitter.py`
- [ ] 2.2 Implement `AsyncPromptSubmitter` class with async HTTP client
- [ ] 2.3 Implement `AsyncPromptSubmitter.submit_prompt()` - async POST /session/{id}/prompt_async
- [ ] 2.4 Support optional message_id generation (UUID) in async context
- [ ] 2.5 Implement abort-before-submit logic in async `submit_prompt(abort=True)`
- [ ] 2.6 Implement `AsyncPromptSubmitter.abort_session()` - async POST /session/{id}/abort

## 3. Async Response Tracking Implementation

- [ ] 3.1 Create `src/opencode_server_client/response/async_poller.py`
- [ ] 3.2 Implement `AsyncResponsePoller` class with async HTTP client
- [ ] 3.3 Implement `AsyncResponsePoller.get_messages()` - async GET /session/{id}/message
- [ ] 3.4 Implement `AsyncResponsePoller.get_message_detail()` - async GET /session/{id}/message/{messageID}
- [ ] 3.5 Implement `AsyncResponsePoller.wait_for_idle()` with async polling
- [ ] 3.6 Handle session not found exceptions appropriately in async context

## 4. Async Main Client Implementation

- [ ] 4.1 Create `src/opencode_server_client/client_async.py`
- [ ] 4.2 Implement `AsyncOpencodeServerClient` class with async manager composition
- [ ] 4.3 Implement async manager property accessors (sessions, prompts, responses)
- [ ] 4.4 Implement async convenience methods: `create_session()`, `list_all_sessions()`, `delete_session()`
- [ ] 4.5 Implement `submit_prompt_and_wait()` async convenience combining submission and polling
- [ ] 4.6 Implement async context manager support (`__aenter__`, `__aexit__`)
- [ ] 4.7 Add logging and error handling throughout async client

## 5. Event Parser Implementation

- [ ] 5.1 Create `src/opencode_server_client/events/parser.py`
- [ ] 5.2 Implement `EventParser` class for parsing SSE data
- [ ] 5.3 Parse `session.status` events to `SessionStatusEvent`
- [ ] 5.4 Parse `session.idle` events to `SessionIdleEvent`
- [ ] 5.5 Parse `message.updated` events to `MessageUpdatedEvent`
- [ ] 5.6 Parse `message.part.updated` events to `MessagePartUpdatedEvent`
- [ ] 5.7 Parse `session.error` events to `SessionErrorEvent`
- [ ] 5.8 Handle unknown event types gracefully (log warning, skip)
- [ ] 5.9 Validate event data against expected schema before returning

## 6. Sync Event Subscription Implementation

- [ ] 6.1 Create `src/opencode_server_client/events/sync_subscriber.py`
- [ ] 6.2 Implement `EventSubscriber` class for sync event handling
- [ ] 6.3 Implement background thread management for SSE connection
- [ ] 6.4 Implement `subscribe(callback, event_types=None)` with event filtering
- [ ] 6.5 Implement `unsubscribe(callback)` to remove callback
- [ ] 6.6 Implement thread-safe callback invocation
- [ ] 6.7 Implement connection lifecycle: connect, listen, disconnect, reconnect on error
- [ ] 6.8 Handle SSE disconnections and automatic reconnection with backoff
- [ ] 6.9 Implement `close()` to cleanly shutdown background thread

## 7. Async Event Subscription Implementation

- [ ] 7.1 Create `src/opencode_server_client/events/async_subscriber.py`
- [ ] 7.2 Implement `AsyncEventSubscriber` class for async event handling
- [ ] 7.3 Implement asyncio task management for SSE connection
- [ ] 7.4 Implement `subscribe(async_callback, event_types=None)` with event filtering
- [ ] 7.5 Implement `unsubscribe(async_callback)` to remove async callback
- [ ] 7.6 Implement coroutine-safe callback invocation
- [ ] 7.7 Implement async connection lifecycle: connect, listen, disconnect, reconnect on error
- [ ] 7.8 Handle SSE disconnections and automatic reconnection with backoff
- [ ] 7.9 Implement `close()` to cleanly shutdown asyncio task

## 8. Package Exports & Integration

- [ ] 8.1 Create `src/opencode_server_client/events/__init__.py` with event class exports
- [ ] 8.2 Update `src/opencode_server_client/__init__.py` to export async client classes
- [ ] 8.3 Export EventSubscriber and AsyncEventSubscriber
- [ ] 8.4 Export all event types (SessionStatusEvent, etc.)
- [ ] 8.5 Ensure no import cycles or circular dependencies
- [ ] 8.6 Add type hints to all public methods

## 9. Unit Tests - Async Session Manager

- [ ] 9.1 Create `tests/test_session_manager_async.py`
- [ ] 9.2 Mock async HTTP client for all tests
- [ ] 9.3 Test async create() with minimal params
- [ ] 9.4 Test async create() with title and parent_id
- [ ] 9.5 Test async create() with 400 error
- [ ] 9.6 Test async list() returns session list
- [ ] 9.7 Test async list() with empty directory
- [ ] 9.8 Test async get() with valid session_id
- [ ] 9.9 Test async get() with 404 error
- [ ] 9.10 Test async delete() succeeds
- [ ] 9.11 Test async delete() with 404 error
- [ ] 9.12 Test async get_status() returns correct status
- [ ] 9.13 Test async wait_for_idle() returns True when idle reached
- [ ] 9.14 Test async wait_for_idle() returns False on timeout
- [ ] 9.15 Test async wait_for_idle() raises on session not found

## 10. Unit Tests - Async Prompt Submitter

- [ ] 10.1 Create `tests/test_prompt_submitter_async.py`
- [ ] 10.2 Test async submit_prompt() with text only
- [ ] 10.3 Test async submit_prompt() with agent parameter
- [ ] 10.4 Test async submit_prompt() with system prompt
- [ ] 10.5 Test async submit_prompt() with tools config
- [ ] 10.6 Test async submit_prompt() auto-generates message_id
- [ ] 10.7 Test async submit_prompt() with custom message_id
- [ ] 10.8 Test async submit_prompt() with abort=False (no abort call)
- [ ] 10.9 Test async submit_prompt() with abort=True (abort then submit)
- [ ] 10.10 Test async abort_session() succeeds
- [ ] 10.11 Test async abort_session() with 404 error

## 11. Unit Tests - Async Response Poller

- [ ] 11.1 Create `tests/test_response_poller_async.py`
- [ ] 11.2 Test async get_messages() returns message list
- [ ] 11.3 Test async get_messages() with empty session
- [ ] 11.4 Test async get_messages() with 404 error
- [ ] 11.5 Test async get_message_detail() returns message with parts
- [ ] 11.6 Test async get_message_detail() with 404 error
- [ ] 11.7 Test async wait_for_idle() polls and returns True
- [ ] 11.8 Test async wait_for_idle() returns False on timeout
- [ ] 11.9 Test async wait_for_idle() checks status every poll_interval
- [ ] 11.10 Test async wait_for_idle() raises on session not found

## 12. Unit Tests - Async Main Client

- [ ] 12.1 Create `tests/test_opencode_client_async.py`
- [ ] 12.2 Test async client initialization with defaults
- [ ] 12.3 Test async client initialization with all parameters
- [ ] 12.4 Test async manager property accessors
- [ ] 12.5 Test async convenience methods (create_session, list_all_sessions, delete_session)
- [ ] 12.6 Test async submit_prompt_and_wait() succeeds
- [ ] 12.7 Test async submit_prompt_and_wait() times out
- [ ] 12.8 Test async submit_prompt_and_wait() with abort=True
- [ ] 12.9 Test async submit_prompt_and_wait() with custom poll_interval
- [ ] 12.10 Test async context manager support (`async with`)

## 13. Unit Tests - Event Parser

- [ ] 13.1 Create `tests/test_event_parser.py`
- [ ] 13.2 Test parse session.status event to SessionStatusEvent
- [ ] 13.3 Test parse session.idle event to SessionIdleEvent
- [ ] 13.4 Test parse message.updated event to MessageUpdatedEvent
- [ ] 13.5 Test parse message.part.updated event to MessagePartUpdatedEvent
- [ ] 13.6 Test parse session.error event to SessionErrorEvent
- [ ] 13.7 Test unknown event type returns None with warning
- [ ] 13.8 Test invalid JSON in event data raises appropriate error
- [ ] 13.9 Test missing required fields in event data raises validation error
- [ ] 13.10 Test event timestamp parsing and formatting

## 14. Unit Tests - Sync Event Subscriber

- [ ] 14.1 Create `tests/test_event_subscriber_sync.py`
- [ ] 14.2 Mock SSE HTTP client for tests
- [ ] 14.3 Test subscribe() registers callback
- [ ] 14.4 Test unsubscribe() removes callback
- [ ] 14.5 Test callback invoked on matching event type
- [ ] 14.6 Test callback NOT invoked when filtered out by event_types
- [ ] 14.7 Test multiple callbacks can be subscribed simultaneously
- [ ] 14.8 Test background thread starts on first subscribe
- [ ] 14.9 Test thread-safe callback invocation (no race conditions)
- [ ] 14.10 Test close() stops background thread gracefully
- [ ] 14.11 Test reconnection with exponential backoff on connection error
- [ ] 14.12 Test callback errors don't crash background thread
- [ ] 14.13 Test EventSubscriber respects event_types filter list

## 15. Unit Tests - Async Event Subscriber

- [ ] 15.1 Create `tests/test_event_subscriber_async.py`
- [ ] 15.2 Mock async SSE HTTP client for tests
- [ ] 15.3 Test async subscribe() registers async callback
- [ ] 15.4 Test async unsubscribe() removes async callback
- [ ] 15.5 Test async callback invoked on matching event type
- [ ] 15.6 Test async callback NOT invoked when filtered out by event_types
- [ ] 15.7 Test multiple async callbacks can be subscribed simultaneously
- [ ] 15.8 Test asyncio task starts on first subscribe
- [ ] 15.9 Test async callback invocation (coroutine execution)
- [ ] 15.10 Test close() stops asyncio task gracefully
- [ ] 15.11 Test reconnection with exponential backoff on connection error
- [ ] 15.12 Test async callback errors don't crash listener task
- [ ] 15.13 Test AsyncEventSubscriber respects event_types filter list
- [ ] 15.14 Test event subscription with async context manager

## 16. Integration Tests

- [ ] 16.1 Create `tests/integration_async.py` for async end-to-end workflows
- [ ] 16.2 Test complete async workflow: create → submit → wait → get messages
- [ ] 16.3 Test async abort and resubmit workflow
- [ ] 16.4 Test async timeout handling in realistic scenarios
- [ ] 16.5 Test async retry logic integration (502 scenario)
- [ ] 16.6 Create `tests/integration_events_sync.py` for sync event testing
- [ ] 16.7 Test sync event subscription receives events in real-time
- [ ] 16.8 Test sync event filtering works correctly
- [ ] 16.9 Test sync event reconnection after disconnect
- [ ] 16.10 Create `tests/integration_events_async.py` for async event testing
- [ ] 16.11 Test async event subscription receives events in real-time
- [ ] 16.12 Test async event filtering works correctly
- [ ] 16.13 Test async event reconnection after disconnect
- [ ] 16.14 Test mixed sync/async usage in same application

## 17. Documentation & Finalization

- [ ] 17.1 Add comprehensive docstrings to all async public methods
- [ ] 17.2 Document async/await patterns in module docstrings
- [ ] 17.3 Add event subscription usage examples to docstrings
- [ ] 17.4 Add type hints to all async parameters and returns
- [ ] 17.5 Run type checker (mypy/pyright) for async code
- [ ] 17.6 Verify all async tests pass with >90% coverage
- [ ] 17.7 Document event types and parsing in README
- [ ] 17.8 Document sync vs. async event subscriber differences
- [ ] 17.9 Add async context manager usage examples
- [ ] 17.10 Update CHANGELOG with async/event features
- [ ] 17.11 Review for consistency with Layers 1-2 conventions
- [ ] 17.12 Document reconnection behavior and backoff strategy
