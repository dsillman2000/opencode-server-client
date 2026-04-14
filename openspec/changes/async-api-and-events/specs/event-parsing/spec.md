## ADDED Requirements

### Requirement: Parse Raw SSE to Typed Events
The system SHALL convert raw SSE events to typed Python objects.

#### Scenario: Parse session status event
- **WHEN** raw SSE contains `{type: "session.status", properties: {sessionID, status}}`
- **THEN** parser returns `SessionStatusEvent(type="session.status", session_id=..., status=...)`

#### Scenario: Parse session idle event
- **WHEN** raw SSE contains `{type: "session.idle", properties: {sessionID}}`
- **THEN** parser returns `SessionIdleEvent(type="session.idle", session_id=...)`

#### Scenario: Parse message updated event
- **WHEN** raw SSE contains `{type: "message.updated", properties: {sessionID, info, ...}}`
- **THEN** parser returns `MessageUpdatedEvent` with message data

#### Scenario: Parse message part updated event
- **WHEN** raw SSE contains `{type: "message.part.updated", properties: {...}}`
- **THEN** parser returns `MessageUpdatedEvent` with part data

#### Scenario: Parse session error event
- **WHEN** raw SSE contains `{type: "session.error", properties: {sessionID, error}}`
- **THEN** parser returns `SessionErrorEvent` with error details

#### Scenario: Unknown event type
- **WHEN** raw SSE contains unknown event type
- **THEN** parser returns generic event object or skips (graceful degradation)

### Requirement: Type-Safe Event Access
The system SHALL provide typed event objects with proper field access.

#### Scenario: Access typed event fields
- **WHEN** user receives `SessionStatusEvent` from subscription
- **THEN** user can access `event.session_id`, `event.status`, `event.type` with type safety

#### Scenario: Pattern match on event type
- **WHEN** user code checks `isinstance(event, SessionStatusEvent)`
- **THEN** type narrowing works in type checkers (mypy, pyright)

#### Scenario: Event has all fields from server
- **WHEN** server sends SSE with all fields
- **THEN** parsed event object contains all fields
