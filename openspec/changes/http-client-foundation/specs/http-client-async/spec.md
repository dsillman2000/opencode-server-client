## ADDED Requirements

### Requirement: Asynchronous HTTP Client Creation
The system SHALL provide an `AsyncHttpClient` class for making asynchronous HTTP requests to the OpenCode server with automatic retry logic.

#### Scenario: Create async client with defaults
- **WHEN** user instantiates `AsyncHttpClient(config)` with `ServerConfig`
- **THEN** async client is ready to make requests with default retry configuration

#### Scenario: Create async client with custom retry config
- **WHEN** user instantiates `AsyncHttpClient(config, retry_config)` with custom `RetryConfig`
- **THEN** async client uses the provided retry parameters for all requests

### Requirement: Async GET Requests with Retry
The system SHALL support asynchronous GET requests with automatic exponential backoff retry on transient failures.

#### Scenario: Async GET succeeds
- **WHEN** user awaits `client.get(path, params=...)` and server responds with 200
- **THEN** coroutine returns response immediately without retries

#### Scenario: Async GET with 502 retry
- **WHEN** user awaits `client.get(path)` and server responds 502 then 200
- **THEN** coroutine retries asynchronously using `asyncio.sleep()` for backoff

#### Scenario: Async GET with TransportError
- **WHEN** user awaits `client.get(path)` and connection fails (TransportError)
- **THEN** coroutine retries with exponential backoff using asyncio

#### Scenario: Async GET exhausts retries
- **WHEN** user awaits `client.get(path)` and server returns 503 on all attempts
- **THEN** final 503 response is returned (raises exception or returns response based on config)

### Requirement: Async POST Requests with Retry
The system SHALL support asynchronous POST requests with automatic exponential backoff retry on transient failures.

#### Scenario: Async POST with JSON body
- **WHEN** user awaits `client.post(path, json={...})` and server responds with 200
- **THEN** coroutine returns response immediately

#### Scenario: Async POST retries on 503
- **WHEN** user awaits `client.post(path, json={...})` and server returns 503 then 200
- **THEN** coroutine retries using asyncio.sleep()

### Requirement: Async DELETE Requests with Retry
The system SHALL support asynchronous DELETE requests with automatic exponential backoff retry on transient failures.

#### Scenario: Async DELETE succeeds
- **WHEN** user awaits `client.delete(path)` and server responds with 200
- **THEN** coroutine returns response immediately

#### Scenario: Async DELETE with transient failure
- **WHEN** user awaits `client.delete(path)` and server responds 502 then 200
- **THEN** coroutine retries asynchronously

### Requirement: Async Directory Context Header
The system SHALL automatically include `X-Opencode-Directory` header in async requests.

#### Scenario: Async request with directory
- **WHEN** user awaits any request method with `directory` parameter
- **THEN** `X-Opencode-Directory` header is included

#### Scenario: Async request without directory
- **WHEN** user awaits any request method without `directory` parameter
- **THEN** `X-Opencode-Directory` header is not included

### Requirement: Async Client Context Manager
The system SHALL support use as async context manager for resource cleanup.

#### Scenario: Use async client in async with statement
- **WHEN** user uses `async with AsyncHttpClient(...) as client:` pattern
- **THEN** async client resources are properly closed on exit
