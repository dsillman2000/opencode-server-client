## ADDED Requirements

### Requirement: Create Session
The system SHALL allow users to create a new session in a directory.

#### Scenario: Create session with minimal parameters
- **WHEN** user calls `SessionManager.create(directory="/path/to/project")`
- **THEN** system POSTs to `/session?directory=...` and returns `SessionMetadata` with auto-generated id and timestamp

#### Scenario: Create session with title
- **WHEN** user calls `SessionManager.create(directory="...", title="My Session")`
- **THEN** system creates session with provided title in metadata

#### Scenario: Create child session
- **WHEN** user calls `SessionManager.create(directory="...", parent_id="session-123")`
- **THEN** system creates session with parent_id relationship

#### Scenario: Create session fails with 400
- **WHEN** user calls `SessionManager.create()` and server responds 400
- **THEN** `SessionCreationError` is raised

#### Scenario: Session creation retries on 502
- **WHEN** user creates session and server responds 502 then 200
- **THEN** system retries per HTTP client retry logic and returns SessionMetadata

### Requirement: List Sessions
The system SHALL allow users to list all sessions in a directory.

#### Scenario: List sessions in directory
- **WHEN** user calls `SessionManager.list(directory="/path")`
- **THEN** system GETs `/session?directory=...` and returns `List[SessionMetadata]`

#### Scenario: List sessions returns empty
- **WHEN** user lists sessions in empty directory
- **THEN** system returns empty list (not error)

#### Scenario: List sessions uses retry logic
- **WHEN** user calls `list()` and server returns 502 then 200 with session list
- **THEN** system retries and returns session list

### Requirement: Get Session
The system SHALL allow users to retrieve a specific session by ID.

#### Scenario: Get session by ID
- **WHEN** user calls `SessionManager.get(session_id="sess-123")`
- **THEN** system GETs `/session/sess-123` and returns `SessionMetadata`

#### Scenario: Get non-existent session
- **WHEN** user calls `SessionManager.get(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised

#### Scenario: Get session with directory context
- **WHEN** user calls `SessionManager.get(session_id="...", directory="...")`
- **THEN** request includes `X-Opencode-Directory` header

### Requirement: Delete Session
The system SHALL allow users to delete a session.

#### Scenario: Delete session succeeds
- **WHEN** user calls `SessionManager.delete(session_id="sess-123")`
- **THEN** system DELETEs `/session/sess-123` and returns True

#### Scenario: Delete non-existent session
- **WHEN** user calls `SessionManager.delete(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised

#### Scenario: Delete session retries on 502
- **WHEN** user deletes session and server responds 502 then 200
- **THEN** system retries and returns True

### Requirement: Default Directory Context
The system SHALL support optional default directory at SessionManager level.

#### Scenario: Manager created with default directory
- **WHEN** user creates `SessionManager(client, directory="/home/projects")`
- **THEN** all operations use this directory unless overridden

#### Scenario: Operation overrides default directory
- **WHEN** user calls `SessionManager.list(directory="/other")` with default directory set
- **THEN** request uses provided `/other` directory (not default)

#### Scenario: No default directory
- **WHEN** user creates `SessionManager(client)` without default
- **THEN** operations require explicit directory parameter
