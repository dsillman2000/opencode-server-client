## ADDED Requirements

### Requirement: Synchronous HTTP Client Creation
The system SHALL provide a `SyncHttpClient` class for making synchronous HTTP requests to the OpenCode server with automatic retry logic.

#### Scenario: Create client with defaults
- **WHEN** user instantiates `SyncHttpClient(config)` with `ServerConfig` containing base_url and optional basic_auth
- **THEN** client is ready to make requests with default retry configuration (3 retries, 0.5s initial delay, 30s max delay, 2.0 exponential base)

#### Scenario: Create client with custom retry config
- **WHEN** user instantiates `SyncHttpClient(config, retry_config)` with custom `RetryConfig`
- **THEN** client uses the provided retry parameters for all requests

### Requirement: GET Requests with Retry
The system SHALL support synchronous GET requests with automatic exponential backoff retry on transient failures.

#### Scenario: Successful GET
- **WHEN** user calls `client.get(path, params=...)` and server responds with 200
- **THEN** response is returned immediately without retries

#### Scenario: GET fails with 502, then succeeds
- **WHEN** user calls `client.get(path)` and server responds 502, then 200 on retry
- **THEN** client automatically retries with exponential backoff and returns 200 response

#### Scenario: GET exhausts retries
- **WHEN** user calls `client.get(path)` and server returns 502 on all attempts (up to max_retries)
- **THEN** final 502 response is returned (no exception raised)

#### Scenario: GET fails with TransportError
- **WHEN** user calls `client.get(path)` and connection is reset (TransportError)
- **THEN** client retries with exponential backoff

#### Scenario: GET with 404 is not retried
- **WHEN** user calls `client.get(path)` and server responds with 404
- **THEN** response is returned immediately without retries (404 is not transient)

### Requirement: POST Requests with Retry
The system SHALL support synchronous POST requests with automatic exponential backoff retry on transient failures.

#### Scenario: Successful POST with JSON body
- **WHEN** user calls `client.post(path, json={...})` and server responds with 200
- **THEN** response is returned immediately

#### Scenario: POST with 503 retries
- **WHEN** user calls `client.post(path, json={...})` and server returns 503 repeatedly
- **THEN** client retries with exponential backoff until success or max_retries exceeded

### Requirement: DELETE Requests with Retry
The system SHALL support synchronous DELETE requests with automatic exponential backoff retry on transient failures.

#### Scenario: Successful DELETE
- **WHEN** user calls `client.delete(path)` and server responds with 200
- **THEN** response is returned immediately

#### Scenario: DELETE with transient failure
- **WHEN** user calls `client.delete(path)` and server responds 502 then 200
- **THEN** client retries and returns success response

### Requirement: Directory Context Header
The system SHALL automatically include `X-Opencode-Directory` header when directory context is provided.

#### Scenario: Request with directory context
- **WHEN** user calls any request method with `directory` parameter set
- **THEN** `X-Opencode-Directory` header is included in the request

#### Scenario: Request without directory context
- **WHEN** user calls any request method without `directory` parameter
- **THEN** `X-Opencode-Directory` header is not included

### Requirement: Exponential Backoff Formula
The system SHALL compute backoff delays using exponential formula with configurable cap.

#### Scenario: Backoff calculation
- **WHEN** retry attempt N occurs where N >= 1
- **THEN** delay = min(initial_delay * (exponential_base ^ N), max_delay) seconds

#### Scenario: First retry uses initial delay
- **WHEN** first retry occurs (N=1)
- **THEN** delay = initial_delay

#### Scenario: Delay caps at max_delay
- **WHEN** calculated delay exceeds max_delay
- **THEN** delay is capped at max_delay

### Requirement: Client Context Manager
The system SHALL support use as context manager for resource cleanup.

#### Scenario: Use client in with statement
- **WHEN** user uses `with SyncHttpClient(...) as client:` pattern
- **THEN** client resources (httpx.Client) are properly closed on exit
