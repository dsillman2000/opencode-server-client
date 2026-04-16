## 1. Shared Event Infrastructure (Layer 2 & 3 Foundation)

- [ ] 1.1 Create `src/opencode_server_client/events/types.py`
- [ ] 1.2 Define `SessionStatusEvent` dataclass (session_id, status: idle/busy/error, timestamp)
- [ ] 1.3 Define `SessionIdleEvent` dataclass (session_id, timestamp)
- [ ] 1.4 Define `MessageUpdatedEvent` dataclass (session_id, message_id, content, timestamp)
- [ ] 1.5 Define `MessagePartUpdatedEvent` dataclass (session_id, message_id, part_index, content, timestamp)
- [ ] 1.6 Define `SessionErrorEvent` dataclass (session_id, error_message, timestamp)
- [ ] 1.7 Create `src/opencode_server_client/events/parser.py`
- [ ] 1.8 Implement `EventParser.parse(raw_sse_data)` - converts raw SSE to typed event objects
- [ ] 1.9 Handle unknown event types gracefully (log, skip)
- [ ] 1.10 Add type hints and docstrings to all event types

## 2. Session Manager Implementation

- [ ] 2.1 Create `src/opencode_server_client/session/sync_manager.py`
- [ ] 2.2 Implement `SessionManager` class with HTTP client and optional default directory
- [ ] 2.3 Implement `SessionManager.create()` - POST /session
- [ ] 2.4 Implement `SessionManager.list()` - GET /session
- [ ] 2.5 Implement `SessionManager.get()` - GET /session/{id}
- [ ] 2.6 Implement `SessionManager.delete()` - DELETE /session/{id}

## 3. Prompt Submission Implementation

- [ ] 3.1 Create `src/opencode_server_client/prompt/sync_submitter.py`
- [ ] 3.2 Implement `PromptSubmitter` class with HTTP client
- [ ] 3.3 Implement `PromptSubmitter.submit_prompt()` - POST /session/{id}/prompt_async
- [ ] 3.4 Support optional message_id generation (UUID)
- [ ] 3.5 Implement abort-before-submit logic in `submit_prompt(abort=True)`
- [ ] 3.6 Implement `PromptSubmitter.abort_session()` - POST /session/{id}/abort

## 4. Sync Event Subscription Implementation

- [ ] 4.1 Create `src/opencode_server_client/events/sync_subscriber.py`
- [ ] 4.2 Implement `EventSubscriber` class for sync SSE handling
- [ ] 4.3 Implement background thread management for SSE stream (`_stream_thread`, `_stop_event`)
- [ ] 4.4 Implement `subscribe(on_event=None, on_idle=None, on_error=None)` callbacks
- [ ] 4.5 Implement `_read_sse_stream()` - background thread reads `/global/event` stream
- [ ] 4.6 Implement event parsing and callback dispatch in thread
- [ ] 4.7 Implement `unsubscribe()` - stops thread and cleans up
- [ ] 4.8 Implement `close()` - gracefully shutdown background thread with timeout
- [ ] 4.9 Implement connection lifecycle: connect, listen, disconnect
- [ ] 4.10 Handle SSE disconnections and automatic reconnection with exponential backoff
- [ ] 4.11 Thread-safe callback invocation and error handling
- [ ] 4.12 Implement filtering: `subscribe(session_id_filter=None)` to filter events by session

## 5. Main Client Implementation

- [ ] 5.1 Create `src/opencode_server_client/client_sync.py`
- [ ] 5.2 Implement `OpencodeServerClient` class with composition of managers
- [ ] 5.3 Implement manager property accessors (sessions, prompts, events)
- [ ] 5.4 Implement convenience methods: `create_session()`, `list_all_sessions()`, `delete_session()`
- [ ] 5.5 Implement `submit_prompt_and_wait()` combining submission and event subscription
- [ ] 5.6 Implement context manager support (`__enter__`, `__exit__`) for cleanup
- [ ] 5.7 Add logging and error handling throughout
- [ ] 5.8 Add type hints to all public methods

## 6. Integration & Package Exports

- [ ] 6.1 Update `src/opencode_server_client/__init__.py` to export all public classes
- [ ] 6.2 Ensure SessionManager, PromptSubmitter, EventSubscriber are importable
- [ ] 6.3 Export all event types (SessionStatusEvent, MessageUpdatedEvent, etc.)
- [ ] 6.4 Verify no import cycles or circular dependencies
- [ ] 6.5 Add comprehensive docstrings to module level

## 7. Unit Tests - Session Manager

- [ ] 7.1 Create `tests/test_session_manager_sync.py`
- [ ] 7.2 Mock HTTP client for all tests
- [ ] 7.3 Test create() with minimal params
- [ ] 7.4 Test create() with title and parent_id
- [ ] 7.5 Test create() with 400 error
- [ ] 7.6 Test list() returns session list
- [ ] 7.7 Test list() with empty directory
- [ ] 7.8 Test get() with valid session_id
- [ ] 7.9 Test get() with 404 error
- [ ] 7.10 Test delete() succeeds
- [ ] 7.11 Test delete() with 404 error
- [ ] 7.12 Test default directory override

## 8. Unit Tests - Prompt Submitter

- [ ] 8.1 Create `tests/test_prompt_submitter_sync.py`
- [ ] 8.2 Test submit_prompt() with text only
- [ ] 8.3 Test submit_prompt() with agent parameter
- [ ] 8.4 Test submit_prompt() with system prompt
- [ ] 8.5 Test submit_prompt() with tools config
- [ ] 8.6 Test submit_prompt() auto-generates message_id
- [ ] 8.7 Test submit_prompt() with custom message_id
- [ ] 8.8 Test submit_prompt() with abort=False (no abort call)
- [ ] 8.9 Test submit_prompt() with abort=True (abort then submit)
- [ ] 8.10 Test abort_session() succeeds
- [ ] 8.11 Test abort_session() with 404 error

## 9. Unit Tests - Event Parser

- [ ] 9.1 Create `tests/test_event_parser.py`
- [ ] 9.2 Test parse SessionStatusEvent from raw SSE
- [ ] 9.3 Test parse SessionIdleEvent from raw SSE
- [ ] 9.4 Test parse MessageUpdatedEvent from raw SSE
- [ ] 9.5 Test parse MessagePartUpdatedEvent from raw SSE
- [ ] 9.6 Test parse SessionErrorEvent from raw SSE
- [ ] 9.7 Test unknown event type returns None with warning
- [ ] 9.8 Test invalid JSON in event data raises appropriate error
- [ ] 9.9 Test missing required fields raises validation error
- [ ] 9.10 Test event timestamp parsing and formatting

## 10. Unit Tests - Sync Event Subscriber

- [ ] 10.1 Create `tests/test_event_subscriber_sync.py`
- [ ] 10.2 Mock SSE HTTP client for tests
- [ ] 10.3 Test subscribe() registers callbacks
- [ ] 10.4 Test unsubscribe() stops background thread
- [ ] 10.5 Test callback invoked on message event
- [ ] 10.6 Test on_idle callback invoked when session idle
- [ ] 10.7 Test on_error callback invoked on error event
- [ ] 10.8 Test multiple callbacks can subscribe simultaneously
- [ ] 10.9 Test background thread starts on first subscribe
- [ ] 10.10 Test thread-safe callback invocation (no race conditions)
- [ ] 10.11 Test close() stops background thread gracefully with timeout
- [ ] 10.12 Test reconnection with exponential backoff on connection error
- [ ] 10.13 Test callback errors don't crash background thread
- [ ] 10.14 Test session_id filtering: only matching events trigger callbacks
- [ ] 10.15 Test SSE stream parsing with multiple events

## 11. Unit Tests - Main Client

- [ ] 11.1 Create `tests/test_opencode_client_sync.py`
- [ ] 11.2 Test client initialization with defaults
- [ ] 11.3 Test client initialization with all parameters
- [ ] 11.4 Test manager property accessors (sessions, prompts, events)
- [ ] 11.5 Test convenience methods (create_session, list_all_sessions, delete_session)
- [ ] 11.6 Test submit_prompt_and_wait() succeeds
- [ ] 11.7 Test submit_prompt_and_wait() times out (on_idle not called)
- [ ] 11.8 Test submit_prompt_and_wait() with abort=True
- [ ] 11.9 Test submit_prompt_and_wait() collects messages from on_message callbacks
- [ ] 11.10 Test context manager support (`with` statement)
- [ ] 11.11 Test cleanup on context manager exit

## 12. Integration Tests

- [ ] 12.1 Create `tests/integration_sync.py` for end-to-end workflows
- [ ] 12.2 Test complete workflow: create → subscribe → submit → wait for idle
- [ ] 12.3 Test receive multiple message events before idle
- [ ] 12.4 Test abort and resubmit workflow with events
- [ ] 12.5 Test timeout handling in realistic scenarios
- [ ] 12.6 Test error event handling during session
- [ ] 12.7 Test concurrent subscriptions (multiple sessions)
- [ ] 12.8 Test SSE reconnection on network hiccup
- [ ] 12.9 Test retry logic integration with HTTP client (502 scenario)

## 13. Documentation & Finalization

- [ ] 13.1 Add comprehensive docstrings to all public methods
- [ ] 13.2 Document sync event subscription patterns in module docstrings
- [ ] 13.3 Document threading model and callback safety
- [ ] 13.4 Add type hints to all parameters and returns
- [ ] 13.5 Run type checker (mypy/pyright)
- [ ] 13.6 Verify all tests pass with >90% coverage
- [ ] 13.7 Update CHANGELOG with new features
- [ ] 13.8 Document event types and parsing
- [ ] 13.9 Document submit_and_wait() convenience method
- [ ] 13.10 Document thread safety and GIL implications
- [ ] 13.11 Review for consistency with Layer 1 conventions
- [ ] 13.12 Add usage examples in docstrings (simple + concurrent workflows)
