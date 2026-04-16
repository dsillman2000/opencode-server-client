# core-data-types Specification

## Purpose
Provide type definitions for session metadata, status, messages, events, worktrees, and exceptions used throughout the SDK.

## Requirements

### Requirement: Session Metadata Type
The system SHALL provide a `SessionMetadata` dataclass representing session information from the server.

#### Scenario: Create SessionMetadata from server response
- **WHEN** server responds with session data: {id, project_id, directory, title, parent_id, version, created_at, updated_at, summary, share_url}
- **THEN** user can construct `SessionMetadata` object with all fields

#### Scenario: Access session ID
- **WHEN** user has a `SessionMetadata` instance
- **THEN** user can access `session.id` field

#### Scenario: Session summary is optional
- **WHEN** session has no summary (just created)
- **THEN** `SessionMetadata.summary` is None

### Requirement: Session Status Type
The system SHALL provide a `SessionStatus` type representing current session state.

#### Scenario: Session is idle
- **WHEN** session status indicates idle state
- **THEN** `SessionStatus(type="idle")` is created

#### Scenario: Session is busy
- **WHEN** session is processing
- **THEN** `SessionStatus(type="busy")` is created

#### Scenario: Session is retrying
- **WHEN** session encountered error and is retrying
- **THEN** `SessionStatus(type="retry", attempt=2, retry_message="...", next_retry_at=123456)` is created

### Requirement: Message Types
The system SHALL provide type definitions for user and assistant messages.

#### Scenario: User message representation
- **WHEN** server returns user message with role="user"
- **THEN** `UserMessage` type contains: id, session_id, role, agent, model, system, tools

#### Scenario: Assistant message representation
- **WHEN** server returns assistant message with role="assistant"
- **THEN** `AssistantMessage` type contains: id, session_id, role, parent_id, model_id, provider_id, cost, tokens, error

#### Scenario: Message union type
- **WHEN** user receives message from server
- **THEN** message is either `UserMessage` or `AssistantMessage` (Message union type)

### Requirement: Event Type Definitions
The system SHALL provide type definitions for server-sent events.

#### Scenario: Session status event
- **WHEN** SSE sends session status update
- **THEN** `SessionStatusEvent` contains: type="session.status", session_id, status

#### Scenario: Session idle event
- **WHEN** SSE sends idle notification
- **THEN** `SessionIdleEvent` contains: type="session.idle", session_id

#### Scenario: Message updated event
- **WHEN** SSE sends message update
- **THEN** `MessageUpdatedEvent` contains: type, session_id, message (optional), part (optional)

#### Scenario: Session error event
- **WHEN** SSE sends error notification
- **THEN** `SessionErrorEvent` contains: type="session.error", session_id, error

### Requirement: Worktree Metadata Type
The system SHALL provide a `WorktreeMetadata` dataclass representing worktree/workspace information.

#### Scenario: Create WorktreeMetadata
- **WHEN** server returns worktree data: {id, name, directory, branch, project_id, vcs, created_at}
- **THEN** user can construct `WorktreeMetadata` object

#### Scenario: Access worktree properties
- **WHEN** user has `WorktreeMetadata` instance
- **THEN** user can access all fields including optional branch and project_id

### Requirement: Exception Types
The system SHALL provide structured exception types for error handling.

#### Scenario: Session creation fails
- **WHEN** session creation fails
- **THEN** `SessionCreationError` is raised

#### Scenario: Session not found
- **WHEN** accessing non-existent session
- **THEN** `SessionNotFoundError` is raised

#### Scenario: Retry exhausted
- **WHEN** all retry attempts fail
- **THEN** `RetryExhaustedError` is raised

#### Scenario: Other errors
- **WHEN** various error conditions occur
- **THEN** `OpencodeError` (base), `PromptSubmissionError`, `WorktreeError`, `EventStreamError` are available
