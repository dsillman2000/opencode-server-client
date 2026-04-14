## 1. Session Manager Implementation

- [ ] 1.1 Create `src/opencode_server_client/session/sync_manager.py`
- [ ] 1.2 Implement `SessionManager` class with HTTP client and optional default directory
- [ ] 1.3 Implement `SessionManager.create()` - POST /session
- [ ] 1.4 Implement `SessionManager.list()` - GET /session
- [ ] 1.5 Implement `SessionManager.get()` - GET /session/{id}
- [ ] 1.6 Implement `SessionManager.delete()` - DELETE /session/{id}
- [ ] 1.7 Implement `SessionManager.get_status()` - GET /session/status with session_id extraction
- [ ] 1.8 Implement `SessionManager.wait_for_idle()` with timeout and poll_interval

## 2. Prompt Submission Implementation

- [ ] 2.1 Create `src/opencode_server_client/prompt/sync_submitter.py`
- [ ] 2.2 Implement `PromptSubmitter` class with HTTP client
- [ ] 2.3 Implement `PromptSubmitter.submit_prompt()` - POST /session/{id}/prompt_async
- [ ] 2.4 Support optional message_id generation (UUID)
- [ ] 2.5 Implement abort-before-submit logic in `submit_prompt(abort=True)`
- [ ] 2.6 Implement `PromptSubmitter.abort_session()` - POST /session/{id}/abort

## 3. Response Tracking Implementation

- [ ] 3.1 Create `src/opencode_server_client/response/sync_poller.py`
- [ ] 3.2 Implement `ResponsePoller` class with HTTP client
- [ ] 3.3 Implement `ResponsePoller.get_messages()` - GET /session/{id}/message
- [ ] 3.4 Implement `ResponsePoller.get_message_detail()` - GET /session/{id}/message/{messageID}
- [ ] 3.5 Implement `ResponsePoller.wait_for_idle()` with timeout/poll_interval
- [ ] 3.6 Handle session not found exceptions appropriately

## 4. Main Client Implementation

- [ ] 4.1 Create `src/opencode_server_client/client_sync.py`
- [ ] 4.2 Implement `OpencodeServerClient` class with composition of managers
- [ ] 4.3 Implement manager property accessors (sessions, prompts, responses)
- [ ] 4.4 Implement convenience methods: `create_session()`, `list_all_sessions()`, `delete_session()`
- [ ] 4.5 Implement `submit_prompt_and_wait()` combining submission and polling
- [ ] 4.6 Implement context manager support (`__enter__`, `__exit__`)
- [ ] 4.7 Add logging and error handling throughout

## 5. Integration & Package Exports

- [ ] 5.1 Update `src/opencode_server_client/__init__.py` to export all public classes
- [ ] 5.2 Ensure SessionManager, PromptSubmitter, ResponsePoller are importable
- [ ] 5.3 Verify no import cycles or circular dependencies
- [ ] 5.4 Add type hints to all public methods

## 6. Unit Tests - Session Manager

- [ ] 6.1 Create `tests/test_session_manager_sync.py`
- [ ] 6.2 Mock HTTP client for all tests
- [ ] 6.3 Test create() with minimal params
- [ ] 6.4 Test create() with title and parent_id
- [ ] 6.5 Test create() with 400 error
- [ ] 6.6 Test list() returns session list
- [ ] 6.7 Test list() with empty directory
- [ ] 6.8 Test get() with valid session_id
- [ ] 6.9 Test get() with 404 error
- [ ] 6.10 Test delete() succeeds
- [ ] 6.11 Test delete() with 404 error
- [ ] 6.12 Test get_status() returns correct status
- [ ] 6.13 Test wait_for_idle() returns True when idle reached
- [ ] 6.14 Test wait_for_idle() returns False on timeout
- [ ] 6.15 Test wait_for_idle() raises on session not found
- [ ] 6.16 Test default directory override

## 7. Unit Tests - Prompt Submitter

- [ ] 7.1 Create `tests/test_prompt_submitter_sync.py`
- [ ] 7.2 Test submit_prompt() with text only
- [ ] 7.3 Test submit_prompt() with agent parameter
- [ ] 7.4 Test submit_prompt() with system prompt
- [ ] 7.5 Test submit_prompt() with tools config
- [ ] 7.6 Test submit_prompt() auto-generates message_id
- [ ] 7.7 Test submit_prompt() with custom message_id
- [ ] 7.8 Test submit_prompt() with abort=False (no abort call)
- [ ] 7.9 Test submit_prompt() with abort=True (abort then submit)
- [ ] 7.10 Test abort_session() succeeds
- [ ] 7.11 Test abort_session() with 404 error

## 8. Unit Tests - Response Poller

- [ ] 8.1 Create `tests/test_response_poller_sync.py`
- [ ] 8.2 Test get_messages() returns message list
- [ ] 8.3 Test get_messages() with empty session
- [ ] 8.4 Test get_messages() with 404 error
- [ ] 8.5 Test get_message_detail() returns message with parts
- [ ] 8.6 Test get_message_detail() with 404 error
- [ ] 8.7 Test wait_for_idle() polls and returns True
- [ ] 8.8 Test wait_for_idle() returns False on timeout
- [ ] 8.9 Test wait_for_idle() checks status every poll_interval
- [ ] 8.10 Test wait_for_idle() raises on session not found

## 9. Unit Tests - Main Client

- [ ] 9.1 Create `tests/test_opencode_client_sync.py`
- [ ] 9.2 Test client initialization with defaults
- [ ] 9.3 Test client initialization with all parameters
- [ ] 9.4 Test manager property accessors
- [ ] 9.5 Test convenience methods (create_session, list_all_sessions, delete_session)
- [ ] 9.6 Test submit_prompt_and_wait() succeeds
- [ ] 9.7 Test submit_prompt_and_wait() times out
- [ ] 9.8 Test submit_prompt_and_wait() with abort=True
- [ ] 9.9 Test submit_prompt_and_wait() with custom poll_interval
- [ ] 9.10 Test context manager support

## 10. Integration Tests

- [ ] 10.1 Create `tests/integration_sync.py` for end-to-end workflows
- [ ] 10.2 Test complete workflow: create → submit → wait → get messages
- [ ] 10.3 Test abort and resubmit workflow
- [ ] 10.4 Test timeout handling in realistic scenarios
- [ ] 10.5 Test retry logic integration (502 scenario)

## 11. Documentation & Finalization

- [ ] 11.1 Add docstrings to all public methods
- [ ] 11.2 Document usage patterns in module docstrings
- [ ] 11.3 Add type hints to all parameters and returns
- [ ] 11.4 Run type checker (mypy/pyright)
- [ ] 11.5 Verify all tests pass with >90% coverage
- [ ] 11.6 Update CHANGELOG with new features
- [ ] 11.7 Document default timeout recommendations
- [ ] 11.8 Review for consistency with Layer 1 conventions
