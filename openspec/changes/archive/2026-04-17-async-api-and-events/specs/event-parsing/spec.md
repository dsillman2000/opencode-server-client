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

### Requirement: Parse Session Created Event
The system SHALL parse session.created events when new sessions are created.

#### Scenario: Parse session.created event
- **WHEN** raw SSE contains `{type: "session.created", properties: {sessionID, info, ...}}`
- **THEN** parser returns `SessionCreatedEvent` with session metadata

### Requirement: Parse Session Updated Event
The system SHALL parse session.updated events when session metadata changes.

#### Scenario: Parse session.updated event
- **WHEN** raw SSE contains `{type: "session.updated", properties: {sessionID, info, time}}`
- **THEN** parser returns `SessionUpdatedEvent` with updated info

### Requirement: Parse Message Part Delta Event
The system SHALL parse message.part.delta events for streaming text deltas.

#### Scenario: Parse message.part.delta event
- **WHEN** raw SSE contains `{type: "message.part.delta", properties: {sessionID, messageID, partID, field, delta}}`
- **THEN** parser returns `MessagePartDeltaEvent` with incremental delta

### Requirement: Parse Server Heartbeat Event
The system SHALL parse server.heartbeat events to keep connections alive.

#### Scenario: Parse server.heartbeat event
- **WHEN** raw SSE contains `{type: "server.heartbeat", properties: {timestamp}}`
- **THEN** parser returns `ServerHeartbeatEvent`

### Requirement: Parse Session Diff Event
The system SHALL parse session.diff events for state change notifications.

#### Scenario: Parse session.diff event
- **WHEN** raw SSE contains `{type: "session.diff", properties: {sessionID, diff, timestamp}}`
- **THEN** parser returns `SessionDiffEvent`

### Requirement: Parse Server Connected Event
The system SHALL parse server.connected events when connection is established.

#### Scenario: Parse server.connected event
- **WHEN** raw SSE contains `{type: "server.connected", properties: {timestamp}}`
- **THEN** parser returns `ServerConnectedEvent`
