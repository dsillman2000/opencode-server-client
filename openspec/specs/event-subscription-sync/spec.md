# Event Subscription (Sync) Specification

## Purpose

Subscribe to Server-Sent Events using background threads.

## Requirements

### Requirement: Synchronous Event Subscription
The system SHALL allow users to subscribe to SSE events synchronously with background thread.

#### Scenario: Subscribe to events
- **WHEN** user calls `EventSubscriber.subscribe(callback=my_func, error_handler=my_error_func, directory="...")`
- **THEN** system returns `EventSubscription` context manager; background thread starts reading `/global/event`

#### Scenario: Callback on each event
- **WHEN** SSE delivers an event
- **THEN** system parses event and invokes `callback(typed_event)` in background thread

#### Scenario: Error callback
- **WHEN** SSE stream encounters error
- **THEN** system invokes `error_handler(exception)` in background thread

#### Scenario: Close subscription
- **WHEN** user calls `subscription.close()` or exits context manager
- **THEN** background thread is cleanly stopped; SSE connection closed

#### Scenario: Use subscription as context manager
- **WHEN** user uses `with EventSubscription(...) as sub:`
- **THEN** event stream starts on enter, stops on exit

#### Scenario: Filter events by session
- **WHEN** user calls `EventSubscriber.subscribe_session_events(session_id="sess-123", callback=...)`
- **THEN** system filters events client-side (only session_id="sess-123" passed to callback)

### Requirement: Sync Callback Context
The system SHALL invoke sync callbacks in background thread.

#### Scenario: Callback executes in thread
- **WHEN** SSE event arrives and callback is invoked
- **THEN** callback code runs in background thread (not blocking main thread)

#### Scenario: Callback may do I/O
- **WHEN** callback performs file I/O, database writes, etc.
- **THEN** background thread handles blocking without freezing application