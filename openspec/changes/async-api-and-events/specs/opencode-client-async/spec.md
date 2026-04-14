## ADDED Requirements

### Requirement: Async Main Client Initialization
The system SHALL provide `AsyncOpencodeServerClient` as primary async entry point.

#### Scenario: Create async client
- **WHEN** user creates `AsyncOpencodeServerClient(base_url="...", basic_auth="...", retry_config=..., default_directory="...")`
- **THEN** async client is ready with async managers

#### Scenario: Async client context manager
- **WHEN** user uses `async with AsyncOpencodeServerClient(...) as client:`
- **THEN** async client resources are properly cleaned up on exit

#### Scenario: Access async managers
- **WHEN** user has async client instance
- **THEN** user can access `client.sessions`, `client.prompts`, `client.responses` async managers

### Requirement: Async Manager Operations
The system SHALL provide async equivalents of all sync manager methods.

#### Scenario: Create session via async client
- **WHEN** user awaits `client.create_session(title="...")`
- **THEN** method delegates to `client.sessions.create()`

#### Scenario: List sessions via async client
- **WHEN** user awaits `client.list_all_sessions()`
- **THEN** method delegates to `client.sessions.list()`

#### Scenario: Delete session via async client
- **WHEN** user awaits `client.delete_session(session_id="...")`
- **THEN** method delegates to `client.sessions.delete()`

### Requirement: Async Submit and Wait Convenience
The system SHALL provide async version of submit_and_wait.

#### Scenario: Async submit and wait
- **WHEN** user awaits `client.submit_prompt_and_wait(session_id="...", prompt_text="...", model={...})`
- **THEN** coroutine submits, polls asynchronously, returns (success: bool, messages: List[Message])

#### Scenario: Async submit and wait with all parameters
- **WHEN** user awaits with abort=True, timeout=600, poll_interval=0.2
- **THEN** all parameters pass through correctly

### Requirement: Async Client Export
The system SHALL export AsyncOpencodeServerClient from main package.

#### Scenario: Import async client
- **WHEN** user imports `from opencode_server_client import AsyncOpencodeServerClient`
- **THEN** class is available
