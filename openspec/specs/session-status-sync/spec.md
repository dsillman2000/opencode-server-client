# session-status-sync Specification

## Purpose
TBD - created by archiving change sync-session-api. Update Purpose after archive.
## Requirements
### Requirement: Get Session Status
The system SHALL allow users to retrieve the current status of sessions.

#### Scenario: Get status for single session
- **WHEN** user calls `SessionManager.get_status(session_id="sess-123")`
- **THEN** system GETs `/session/status?directory=...` (returns dict of all statuses) and extracts status for that session

#### Scenario: Session status is idle
- **WHEN** session has completed processing
- **THEN** returned status has `type="idle"`

#### Scenario: Session status is busy
- **WHEN** session is processing a prompt
- **THEN** returned status has `type="busy"`

#### Scenario: Session status is retry
- **WHEN** session encountered error and is retrying
- **THEN** returned status has `type="retry"` with `attempt`, `retry_message`, `next_retry_at` fields

#### Scenario: Get status for missing session
- **WHEN** user calls `get_status(session_id="invalid")` and session not in response
- **THEN** `SessionNotFoundError` is raised

### Requirement: Poll Until Session Idle
The system SHALL allow users to block until a session reaches idle state.

#### Scenario: Wait for session to become idle
- **WHEN** user calls `ResponsePoller.wait_for_idle(session_id="sess-123", timeout=300, poll_interval=0.5)`
- **THEN** system polls `/session/status` every 0.5 seconds until session type="idle" or timeout exceeded

#### Scenario: Session becomes idle before timeout
- **WHEN** user waits and session reaches idle state after 2 seconds
- **THEN** method returns True immediately (not waiting until timeout)

#### Scenario: Timeout exceeded
- **WHEN** user waits and session is still busy after 300 seconds
- **THEN** method returns False

#### Scenario: Session not found during polling
- **WHEN** user waits and session is deleted (404 response)
- **THEN** `SessionNotFoundError` is raised

#### Scenario: Custom poll interval
- **WHEN** user calls `wait_for_idle(..., poll_interval=0.1)`
- **THEN** system checks status every 0.1 seconds (short interval for testing/low-latency cases)

#### Scenario: Polling uses retry logic
- **WHEN** polling encounters 502 response
- **THEN** HTTP client retries; polling continues transparently

### Requirement: Session Status Monitoring
The system SHALL support checking session status without blocking.

#### Scenario: Get status without waiting
- **WHEN** user calls `get_status()` (without wait)
- **THEN** method returns current status immediately

