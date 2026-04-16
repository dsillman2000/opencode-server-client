## 1. Shared Event Infrastructure (Layer 2 & 3 Foundation)

- [x] 1.1 Create `src/opencode_server_client/events/types.py`
- [x] 1.2 Define `SessionStatusEvent` dataclass (session_id, status: idle/busy/error, timestamp)
- [x] 1.3 Define `SessionIdleEvent` dataclass (session_id, timestamp)
- [x] 1.4 Define `MessageUpdatedEvent` dataclass (session_id, message_id, content, timestamp)
- [x] 1.5 Define `MessagePartUpdatedEvent` dataclass (session_id, message_id, part_index, content, timestamp)
- [x] 1.6 Define `SessionErrorEvent` dataclass (session_id, error_message, timestamp)
- [x] 1.7 Create `src/opencode_server_client/events/parser.py`
- [x] 1.8 Implement `EventParser.parse(raw_sse_data)` - converts raw SSE to typed event objects
- [x] 1.9 Handle unknown event types gracefully (log, skip)
- [x] 1.10 Add type hints and docstrings to all event types

## 2. Session Manager Implementation

- [x] 2.1 Create `src/opencode_server_client/session/sync_manager.py`
- [x] 2.2 Implement `SessionManager` class with HTTP client and optional default directory
- [x] 2.3 Implement `SessionManager.create()` - POST /session
- [x] 2.4 Implement `SessionManager.list()` - GET /session
- [x] 2.5 Implement `SessionManager.get()` - GET /session/{id}
- [x] 2.6 Implement `SessionManager.delete()` - DELETE /session/{id}

## 3. Prompt Submission Implementation

- [x] 3.1 Create `src/opencode_server_client/prompt/sync_submitter.py`
- [x] 3.2 Implement `PromptSubmitter` class with HTTP client
- [x] 3.3 Implement `PromptSubmitter.submit_prompt()` - POST /session/{id}/prompt_async
- [x] 3.4 Support optional message_id generation (UUID)
- [x] 3.5 Implement abort-before-submit logic in `submit_prompt(abort=True)`
- [x] 3.6 Implement `PromptSubmitter.abort_session()` - POST /session/{id}/abort

## 4. Sync Event Subscription Implementation

- [x] 4.1 Create `src/opencode_server_client/events/sync_subscriber.py`
- [x] 4.2 Implement `EventSubscriber` class for sync SSE handling
- [x] 4.3 Implement background thread management for SSE stream (`_stream_thread`, `_stop_event`)
- [x] 4.4 Implement `subscribe(on_event=None, on_idle=None, on_error=None)` callbacks
- [x] 4.5 Implement `_read_sse_stream()` - background thread reads `/global/event` stream
- [x] 4.6 Implement event parsing and callback dispatch in thread
- [x] 4.7 Implement `unsubscribe()` - stops thread and cleans up
- [x] 4.8 Implement `close()` - gracefully shutdown background thread with timeout
- [x] 4.9 Implement connection lifecycle: connect, listen, disconnect
- [x] 4.10 Handle SSE disconnections and automatic reconnection with exponential backoff
- [x] 4.11 Thread-safe callback invocation and error handling
- [x] 4.12 Implement filtering: `subscribe(session_id_filter=None)` to filter events by session

## 5. Main Client Implementation

- [x] 5.1 Create `src/opencode_server_client/client_sync.py`
- [x] 5.2 Implement `OpencodeServerClient` class with composition of managers
- [x] 5.3 Implement manager property accessors (sessions, prompts, events)
- [x] 5.4 Implement convenience methods: `create_session()`, `list_all_sessions()`, `delete_session()`
- [x] 5.5 Implement `submit_prompt_and_wait()` combining submission and event subscription
- [x] 5.6 Implement context manager support (`__enter__`, `__exit__`) for cleanup
- [x] 5.7 Add logging and error handling throughout
- [x] 5.8 Add type hints to all public methods

## 6. Integration & Package Exports

- [x] 6.1 Update `src/opencode_server_client/__init__.py` to export all public classes
- [x] 6.2 Ensure SessionManager, PromptSubmitter, EventSubscriber are importable
- [x] 6.3 Export all event types (SessionStatusEvent, MessageUpdatedEvent, etc.)
- [x] 6.4 Verify no import cycles or circular dependencies
- [x] 6.5 Add comprehensive docstrings to module level

## 7. Unit Tests - Session Manager

- [x] 7.1 Create `tests/test_session_manager_sync.py`
- [x] 7.2 Mock HTTP client for all tests
- [x] 7.3 Test create() with minimal params
- [x] 7.4 Test create() with title and parent_id
- [x] 7.5 Test create() with 400 error
- [x] 7.6 Test list() returns session list
- [x] 7.7 Test list() with empty directory
- [x] 7.8 Test get() with valid session_id
- [x] 7.9 Test get() with 404 error
- [x] 7.10 Test delete() succeeds
- [x] 7.11 Test delete() with 404 error
- [x] 7.12 Test default directory override

## 8. Unit Tests - Prompt Submitter

- [x] 8.1 Create `tests/test_prompt_submitter_sync.py`
- [x] 8.2 Test submit_prompt() with text only
- [x] 8.3 Test submit_prompt() with agent parameter
- [x] 8.4 Test submit_prompt() with system prompt
- [x] 8.5 Test submit_prompt() with tools config
- [x] 8.6 Test submit_prompt() auto-generates message_id
- [x] 8.7 Test submit_prompt() with custom message_id
- [x] 8.8 Test submit_prompt() with abort=False (no abort call)
- [x] 8.9 Test submit_prompt() with abort=True (abort then submit)
- [x] 8.10 Test abort_session() succeeds
- [x] 8.11 Test abort_session() with 404 error

## 9. Unit Tests - Event Parser

- [x] 9.1 Create `tests/test_event_parser.py`
- [x] 9.2 Test parse SessionStatusEvent from raw SSE
- [x] 9.3 Test parse SessionIdleEvent from raw SSE
- [x] 9.4 Test parse MessageUpdatedEvent from raw SSE
- [x] 9.5 Test parse MessagePartUpdatedEvent from raw SSE
- [x] 9.6 Test parse SessionErrorEvent from raw SSE
- [x] 9.7 Test unknown event type returns None with warning
- [x] 9.8 Test invalid JSON in event data raises appropriate error
- [x] 9.9 Test missing required fields raises validation error
- [x] 9.10 Test event timestamp parsing and formatting

## 10. Unit Tests - Sync Event Subscriber

- [x] 10.1 Create `tests/test_event_subscriber_sync.py`
- [x] 10.2 Mock SSE HTTP client for tests
- [x] 10.3 Test subscribe() registers callbacks
- [x] 10.4 Test unsubscribe() stops background thread
- [x] 10.5 Test callback invoked on message event
- [x] 10.6 Test on_idle callback invoked when session idle
- [x] 10.7 Test on_error callback invoked on error event
- [x] 10.8 Test multiple callbacks can subscribe simultaneously
- [x] 10.9 Test background thread starts on first subscribe
- [x] 10.10 Test thread-safe callback invocation (no race conditions)
- [x] 10.11 Test close() stops background thread gracefully with timeout
- [x] 10.12 Test reconnection with exponential backoff on connection error
- [x] 10.13 Test callback errors don't crash background thread
- [x] 10.14 Test session_id filtering: only matching events trigger callbacks
- [x] 10.15 Test SSE stream parsing with multiple events

## 11. Unit Tests - Main Client

- [x] 11.1 Create `tests/test_opencode_client_sync.py`
- [x] 11.2 Test client initialization with defaults
- [x] 11.3 Test client initialization with all parameters
- [x] 11.4 Test manager property accessors (sessions, prompts, events)
- [x] 11.5 Test convenience methods (create_session, list_all_sessions, delete_session)
- [x] 11.6 Test submit_prompt_and_wait() succeeds
- [x] 11.7 Test submit_prompt_and_wait() times out (on_idle not called)
- [x] 11.8 Test submit_prompt_and_wait() with abort=True
- [x] 11.9 Test submit_prompt_and_wait() collects messages from on_message callbacks
- [x] 11.10 Test context manager support (`with` statement)
- [x] 11.11 Test cleanup on context manager exit

## 12. Integration Tests

- [x] 12.1 Create `tests/integration_sync.py` for end-to-end workflows
- [x] 12.2 Test complete workflow: create → subscribe → submit → wait for idle
- [x] 12.3 Test receive multiple message events before idle
- [x] 12.4 Test abort and resubmit workflow with events
- [x] 12.5 Test timeout handling in realistic scenarios
- [x] 12.6 Test error event handling during session
- [x] 12.7 Test concurrent subscriptions (multiple sessions)
- [x] 12.8 Test SSE reconnection on network hiccup
- [x] 12.9 Test retry logic integration with HTTP client (502 scenario)

## 13. Documentation & Finalization

- [x] 13.1 Add comprehensive docstrings to all public methods
- [x] 13.2 Document sync event subscription patterns in module docstrings
- [x] 13.3 Document threading model and callback safety
- [x] 13.4 Add type hints to all parameters and returns
- [x] 13.5 Run type checker (mypy/pyright)
- [x] 13.6 Verify all tests pass with >90% coverage
- [x] 13.7 Update CHANGELOG with new features
- [x] 13.8 Document event types and parsing
- [x] 13.9 Document submit_and_wait() convenience method
- [x] 13.10 Document thread safety and GIL implications
- [x] 13.11 Review for consistency with Layer 1 conventions
- [x] 13.12 Add usage examples in docstrings (simple + concurrent workflows)
