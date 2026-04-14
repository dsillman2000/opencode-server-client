## 1. Project Structure & Configuration

- [ ] 1.1 Create module structure: `src/opencode_server_client/http_client/`
- [ ] 1.2 Create `__init__.py` files for package hierarchy
- [ ] 1.3 Add `httpx` to `pyproject.toml` dependencies if not already present
- [ ] 1.4 Create `src/opencode_server_client/config.py` for ServerConfig and RetryConfig dataclasses

## 2. Configuration & Type Definitions

- [ ] 2.1 Implement `ServerConfig` dataclass (base_url, basic_auth, timeout)
- [ ] 2.2 Implement `RetryConfig` dataclass (max_retries, initial_delay, max_delay, exponential_base)
- [ ] 2.3 Add validation to RetryConfig (exponential_base > 1.0)
- [ ] 2.4 Create `src/opencode_server_client/types.py` module
- [ ] 2.5 Implement `SessionMetadata` dataclass
- [ ] 2.6 Implement `SessionStatus` type (Union of idle/busy/retry variants)
- [ ] 2.7 Implement `UserMessage` and `AssistantMessage` dataclasses
- [ ] 2.8 Implement `WorktreeMetadata` dataclass
- [ ] 2.9 Implement event types: `SessionStatusEvent`, `SessionIdleEvent`, `MessageUpdatedEvent`, `SessionErrorEvent`

## 3. Exception Hierarchy

- [ ] 3.1 Create `src/opencode_server_client/exceptions.py`
- [ ] 3.2 Implement base exception: `OpencodeError`
- [ ] 3.3 Implement session exceptions: `SessionError`, `SessionCreationError`, `SessionNotFoundError`
- [ ] 3.4 Implement other exceptions: `PromptSubmissionError`, `WorktreeError`, `EventStreamError`, `RetryExhaustedError`

## 4. Synchronous HTTP Client

- [ ] 4.1 Create `src/opencode_server_client/http_client/sync_client.py`
- [ ] 4.2 Implement `SyncHttpClient` class initialization with ServerConfig and RetryConfig
- [ ] 4.3 Implement exponential backoff delay calculation
- [ ] 4.4 Implement retry logic wrapper function (applies backoff between attempts)
- [ ] 4.5 Implement `SyncHttpClient.get()` method with retry logic
- [ ] 4.6 Implement `SyncHttpClient.post()` method with retry logic
- [ ] 4.7 Implement `SyncHttpClient.delete()` method with retry logic
- [ ] 4.8 Implement `SyncHttpClient.request()` generic method
- [ ] 4.9 Add `X-Opencode-Directory` header support in all methods
- [ ] 4.10 Implement context manager support (`__enter__`, `__exit__`)
- [ ] 4.11 Add logging for retry attempts (debug level)

## 5. Asynchronous HTTP Client

- [ ] 5.1 Create `src/opencode_server_client/http_client/async_client.py`
- [ ] 5.2 Implement `AsyncHttpClient` class initialization with ServerConfig and RetryConfig
- [ ] 5.3 Implement async exponential backoff delay calculation
- [ ] 5.4 Implement async retry logic wrapper (uses asyncio.sleep())
- [ ] 5.5 Implement `AsyncHttpClient.get()` async method with retry logic
- [ ] 5.6 Implement `AsyncHttpClient.post()` async method with retry logic
- [ ] 5.7 Implement `AsyncHttpClient.delete()` async method with retry logic
- [ ] 5.8 Implement `AsyncHttpClient.request()` generic async method
- [ ] 5.9 Add `X-Opencode-Directory` header support in all async methods
- [ ] 5.10 Implement async context manager support (`__aenter__`, `__aexit__`)
- [ ] 5.11 Add logging for async retry attempts (debug level)

## 6. Testing - Sync Client

- [ ] 6.1 Create `tests/test_http_client_sync.py`
- [ ] 6.2 Test successful GET/POST/DELETE without retries
- [ ] 6.3 Test GET/POST/DELETE with single 502 then success
- [ ] 6.4 Test 503 retry behavior
- [ ] 6.5 Test TransportError retry behavior
- [ ] 6.6 Test 404 is NOT retried
- [ ] 6.7 Test retry exhaustion (max retries exceeded)
- [ ] 6.8 Test exponential backoff delay calculation
- [ ] 6.9 Test X-Opencode-Directory header inclusion
- [ ] 6.10 Test context manager cleanup
- [ ] 6.11 Test custom retry configuration

## 7. Testing - Async Client

- [ ] 7.1 Create `tests/test_http_client_async.py`
- [ ] 7.2 Test async GET/POST/DELETE without retries
- [ ] 7.3 Test async 502 retry with asyncio.sleep()
- [ ] 7.4 Test async 503 retry behavior
- [ ] 7.5 Test async TransportError retry behavior
- [ ] 7.6 Test async retry exhaustion
- [ ] 7.7 Test X-Opencode-Directory header in async requests
- [ ] 7.8 Test async context manager cleanup
- [ ] 7.9 Test custom retry configuration

## 8. Testing - Types & Configuration

- [ ] 8.1 Create `tests/test_config.py`
- [ ] 8.2 Test ServerConfig creation and immutability
- [ ] 8.3 Test RetryConfig creation with defaults
- [ ] 8.4 Test RetryConfig validation (exponential_base > 1.0)
- [ ] 8.5 Create `tests/test_types.py`
- [ ] 8.6 Test all dataclass instantiations
- [ ] 8.7 Test event type creation
- [ ] 8.8 Create `tests/test_exceptions.py`
- [ ] 8.9 Test exception hierarchy and raising

## 9. Documentation & Integration

- [ ] 9.1 Create `src/opencode_server_client/__init__.py` with public exports
- [ ] 9.2 Document ServerConfig and RetryConfig in module docstrings
- [ ] 9.3 Document retry behavior in SyncHttpClient/AsyncHttpClient
- [ ] 9.4 Add type hints to all public methods
- [ ] 9.5 Create basic CHANGELOG entry for this change
- [ ] 9.6 Verify all tests pass
- [ ] 9.7 Run type checker (mypy/pyright) on new code

## 10. Integration & Cleanup

- [ ] 10.1 Ensure SyncHttpClient and AsyncHttpClient are importable from main package
- [ ] 10.2 Verify no import cycles or missing dependencies
- [ ] 10.3 Review code for consistency with project style
- [ ] 10.4 Check test coverage (aim for >90%)
