## ADDED Requirements

### Requirement: Main Sync Client Initialization
The system SHALL provide `OpencodeServerClient` as the primary entry point for synchronous operations.

#### Scenario: Create client with minimal config
- **WHEN** user creates `OpencodeServerClient(base_url="http://localhost:5000")`
- **THEN** client is ready with default retry config and no default directory

#### Scenario: Create client with full config
- **WHEN** user creates `OpencodeServerClient(base_url="...", basic_auth="...", timeout=120, retry_config=..., default_directory="/path")`
- **THEN** all parameters are applied to underlying HTTP client and managers

#### Scenario: Client exposes manager interfaces
- **WHEN** user has `OpencodeServerClient` instance
- **THEN** user can access `client.sessions`, `client.prompts`, `client.responses` managers

### Requirement: Sync Client Aggregates All Operations
The system SHALL provide convenience methods on main client for common operations.

#### Scenario: Create session via main client
- **WHEN** user calls `client.create_session(title="...")`
- **THEN** delegates to `client.sessions.create()`

#### Scenario: List sessions via main client
- **WHEN** user calls `client.list_all_sessions()`
- **THEN** delegates to `client.sessions.list()`

#### Scenario: Delete session via main client
- **WHEN** user calls `client.delete_session(session_id="...")`
- **THEN** delegates to `client.sessions.delete()`

### Requirement: Client Context Manager Support
The system SHALL support client use as context manager for cleanup.

#### Scenario: Use client in with statement
- **WHEN** user uses `with OpencodeServerClient(...) as client:`
- **THEN** client resources are properly cleaned up on exit

### Requirement: Submit and Wait Convenience
The system SHALL provide ergonomic submit_and_wait method on main client.

#### Scenario: Call submit_and_wait on main client
- **WHEN** user calls `client.submit_prompt_and_wait(session_id="...", prompt_text="...", model={...})`
- **THEN** method submits, polls until idle or timeout, returns (success: bool, messages: List[Message])

#### Scenario: Submit and wait with all parameters
- **WHEN** user calls with abort=True, timeout=600, poll_interval=0.2
- **THEN** all parameters are passed through to underlying operations

### Requirement: Export Main Classes
The system SHALL export all public classes from the main package.

#### Scenario: Import from main package
- **WHEN** user imports `from opencode_server_client import OpencodeServerClient, SessionMetadata, SessionStatus`
- **THEN** classes are available and usable
