## 1. Project Structure & Configuration

- [x] 1.1 Create module structure: `src/opencode_server_client/http_client/`
- [x] 1.2 Create `__init__.py` files for package hierarchy
- [x] 1.3 Add `httpx` to `pyproject.toml` dependencies if not already present
- [x] 1.4 Create `src/opencode_server_client/config.py` for ServerConfig and RetryConfig dataclasses

## 2. Configuration & Type Definitions

- [x] 2.1 Implement `ServerConfig` dataclass (base_url, basic_auth, timeout)
- [x] 2.2 Implement `RetryConfig` dataclass (max_retries, initial_delay, max_delay, exponential_base)
- [x] 2.3 Add validation to RetryConfig (exponential_base > 1.0)
- [x] 2.4 Create `src/opencode_server_client/types.py` module
- [x] 2.5 Implement `SessionMetadata` dataclass
- [x] 2.6 Implement `SessionStatus` type (Union of idle/busy/retry variants)
- [x] 2.7 Implement `UserMessage` and `AssistantMessage` dataclasses
- [x] 2.8 Implement `WorktreeMetadata` dataclass
- [x] 2.9 Implement event types: `SessionStatusEvent`, `SessionIdleEvent`, `MessageUpdatedEvent`, `SessionErrorEvent`

## 3. Exception Hierarchy

- [x] 3.1 Create `src/opencode_server_client/exceptions.py`
- [x] 3.2 Implement base exception: `OpencodeError`
- [x] 3.3 Implement session exceptions: `SessionError`, `SessionCreationError`, `SessionNotFoundError`
- [x] 3.4 Implement other exceptions: `PromptSubmissionError`, `WorktreeError`, `EventStreamError`, `RetryExhaustedError`

## 4. Synchronous HTTP Client

- [x] 4.1 Create `src/opencode_server_client/http_client/sync_client.py`
- [x] 4.2 Implement `SyncHttpClient` class initialization with ServerConfig and RetryConfig
- [x] 4.3 Implement exponential backoff delay calculation
- [x] 4.4 Implement retry logic wrapper function (applies backoff between attempts)
- [x] 4.5 Implement `SyncHttpClient.get()` method with retry logic
- [x] 4.6 Implement `SyncHttpClient.post()` method with retry logic
- [x] 4.7 Implement `SyncHttpClient.delete()` method with retry logic
- [x] 4.8 Implement `SyncHttpClient.request()` generic method
- [x] 4.9 Add `X-Opencode-Directory` header support in all methods
- [x] 4.10 Implement context manager support (`__enter__`, `__exit__`)
- [x] 4.11 Add logging for retry attempts (debug level)

## 5. Asynchronous HTTP Client

- [x] 5.1 Create `src/opencode_server_client/http_client/async_client.py`
- [x] 5.2 Implement `AsyncHttpClient` class initialization with ServerConfig and RetryConfig
- [x] 5.3 Implement async exponential backoff delay calculation
- [x] 5.4 Implement async retry logic wrapper (uses asyncio.sleep())
- [x] 5.5 Implement `AsyncHttpClient.get()` async method with retry logic
- [x] 5.6 Implement `AsyncHttpClient.post()` async method with retry logic
- [x] 5.7 Implement `AsyncHttpClient.delete()` async method with retry logic
- [x] 5.8 Implement `AsyncHttpClient.request()` generic async method
- [x] 5.9 Add `X-Opencode-Directory` header support in all async methods
- [x] 5.10 Implement async context manager support (`__aenter__`, `__aexit__`)
- [x] 5.11 Add logging for async retry attempts (debug level)

## 6. Testing - Sync Client

- [x] 6.1 Create `tests/test_http_client_sync.py`
- [x] 6.2 Test successful GET/POST/DELETE without retries
- [x] 6.3 Test GET/POST/DELETE with single 502 then success
- [x] 6.4 Test 503 retry behavior
- [x] 6.5 Test TransportError retry behavior
- [x] 6.6 Test 404 is NOT retried
- [x] 6.7 Test retry exhaustion (max retries exceeded)
- [x] 6.8 Test exponential backoff delay calculation
- [x] 6.9 Test X-Opencode-Directory header inclusion
- [x] 6.10 Test context manager cleanup
- [x] 6.11 Test custom retry configuration

## 7. Testing - Async Client

- [x] 7.1 Create `tests/test_http_client_async.py`
- [x] 7.2 Test async GET/POST/DELETE without retries
- [x] 7.3 Test async 502 retry with asyncio.sleep()
- [x] 7.4 Test async 503 retry behavior
- [x] 7.5 Test async TransportError retry behavior
- [x] 7.6 Test async retry exhaustion
- [x] 7.7 Test X-Opencode-Directory header in async requests
- [x] 7.8 Test async context manager cleanup
- [x] 7.9 Test custom retry configuration

## 8. Testing - Types & Configuration

- [x] 8.1 Create `tests/test_config.py`
- [x] 8.2 Test ServerConfig creation and immutability
- [x] 8.3 Test RetryConfig creation with defaults
- [x] 8.4 Test RetryConfig validation (exponential_base > 1.0)
- [x] 8.5 Create `tests/test_types.py`
- [x] 8.6 Test all dataclass instantiations
- [x] 8.7 Test event type creation
- [x] 8.8 Create `tests/test_exceptions.py`
- [x] 8.9 Test exception hierarchy and raising

## 9. Documentation & Integration

- [x] 9.1 Create `src/opencode_server_client/__init__.py` with public exports
- [x] 9.2 Document ServerConfig and RetryConfig in module docstrings
- [x] 9.3 Document retry behavior in SyncHttpClient/AsyncHttpClient
- [x] 9.4 Add type hints to all public methods
- [x] 9.5 Create basic CHANGELOG entry for this change
- [x] 9.6 Verify all tests pass
- [x] 9.7 Run type checker (mypy/pyright) on new code

## 10. Integration & Cleanup

- [x] 10.1 Ensure SyncHttpClient and AsyncHttpClient are importable from main package
- [x] 10.2 Verify no import cycles or missing dependencies
- [x] 10.3 Review code for consistency with project style
- [x] 10.4 Check test coverage (aim for >90%)
