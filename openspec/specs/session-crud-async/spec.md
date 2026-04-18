# Async Session CRUD Specification

> **NOTE**: This is the async version of the session-crud-sync specification.

## Purpose

Provides async versions of session CRUD operations for use with asyncio.

## ADDED Requirements

> **NOTE**: Session IDs are generated as 30-character base-62 monotonic identifiers prefixed with `ses_` (e.g., `ses_abc123def456ghijklmnopqr`). This matches OpenCode's native ID semantics using timestamp-derived ordering.

### Requirement: Async Create Session
The system SHALL allow users to asynchronously create a new session.

#### Scenario: Create session with await
- **WHEN** user awaits `AsyncSessionManager.create(directory="/path")`
- **THEN** coroutine POSTs to `/session` and returns `SessionMetadata`

#### Scenario: Create session with title
- **WHEN** user awaits `create(directory="...", title="Session")`
- **THEN** coroutine creates session with title

#### Scenario: Create session with parent_id
- **WHEN** user awaits `create(directory="...", parent_id="sess-123")`
- **THEN** coroutine creates child session

#### Scenario: Session creation error
- **WHEN** user awaits `create()` and server responds 400
- **THEN** `SessionCreationError` is raised (not swallowed)

### Requirement: Async List Sessions
The system SHALL allow users to asynchronously list sessions.

#### Scenario: List sessions with await
- **WHEN** user awaits `AsyncSessionManager.list(directory="/path")`
- **THEN** coroutine GETs `/session` and returns `List[SessionMetadata]`

#### Scenario: List empty directory
- **WHEN** user awaits `list()` for empty directory
- **THEN** coroutine returns empty list

### Requirement: Async Get Session
The system SHALL allow users to asynchronously retrieve a session by ID.

#### Scenario: Get session with await
- **WHEN** user awaits `AsyncSessionManager.get(session_id="sess-123")`
- **THEN** coroutine GETs `/session/sess-123` and returns `SessionMetadata`

#### Scenario: Get non-existent session
- **WHEN** user awaits `get(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised

### Requirement: Async Delete Session
The system SHALL allow users to asynchronously delete a session.

#### Scenario: Delete session with await
- **WHEN** user awaits `AsyncSessionManager.delete(session_id="sess-123")`
- **THEN** coroutine DELETEs `/session/sess-123` and returns True

#### Scenario: Delete non-existent session
- **WHEN** user awaits `delete(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised

### Requirement: Async Get Status
The system SHALL allow users to asynchronously check session status.

#### Scenario: Get status with await
- **WHEN** user awaits `AsyncSessionManager.get_status(session_id="sess-123")`
- **THEN** coroutine GETs `/session/status` and returns `SessionStatus`

### Requirement: Async Wait for Idle
The system SHALL allow users to asynchronously wait for session idle state.

#### Scenario: Wait for idle with await
- **WHEN** user awaits `AsyncSessionManager.wait_for_idle(session_id="sess-123", timeout=300, poll_interval=0.5)`
- **THEN** coroutine polls asynchronously and returns True when idle or False on timeout

#### Scenario: Wait for idle uses asyncio.sleep
- **WHEN** awaiting `wait_for_idle()` with poll_interval=0.1
- **THEN** coroutine uses `await asyncio.sleep(0.1)` between polls (non-blocking)

#### Scenario: Wait for idle detects session not found
- **WHEN** user awaits and session is deleted (404)
- **THEN** `SessionNotFoundError` is raised

### Requirement: Async Update Session
The system SHALL allow users to asynchronously update session metadata.

#### Scenario: Update session title with await
- **WHEN** user awaits `AsyncSessionManager.update(session_id="sess-123", title="New Title")`
- **THEN** coroutine PATCHes `/session/sess-123` and returns updated `SessionMetadata`

#### Scenario: Update multiple fields
- **WHEN** user awaits `update(session_id="sess-123", title="Title", version=2)`
- **THEN** coroutine sends both fields in PATCH request

#### Scenario: Update with no fields raises error
- **WHEN** user awaits `update(session_id="sess-123")` with no parameters
- **THEN** `ValueError` is raised

#### Scenario: Update non-existent session
- **WHEN** user awaits `update(session_id="invalid", title="Test")` and server responds 404
- **THEN** `SessionNotFoundError` is raised