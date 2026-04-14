## ADDED Requirements

### Requirement: Asynchronous Event Subscription
The system SHALL allow users to subscribe to SSE events asynchronously.

#### Scenario: Async subscribe to events
- **WHEN** user awaits `AsyncEventSubscriber.subscribe(callback=my_async_func, error_handler=my_error_func)`
- **THEN** system returns `AsyncEventSubscription` context manager; asyncio task starts reading `/global/event`

#### Scenario: Async callback on each event
- **WHEN** SSE delivers event and system parses it
- **THEN** system awaits `callback(typed_event)` within asyncio task

#### Scenario: Async error callback
- **WHEN** SSE stream encounters error
- **THEN** system awaits `error_handler(exception)` within asyncio task

#### Scenario: Close async subscription
- **WHEN** user calls `await subscription.close()` or exits `async with` block
- **THEN** asyncio task is cancelled; SSE connection closed

#### Scenario: Use subscription as async context manager
- **WHEN** user uses `async with AsyncEventSubscription(...) as sub:`
- **THEN** event stream starts on enter, stops on exit

#### Scenario: Async subscribe with filtering
- **WHEN** user awaits `AsyncEventSubscriber.subscribe_session_events(session_id="...", callback=...)`
- **THEN** system filters events client-side to specific session

#### Scenario: Callback may await
- **WHEN** async callback uses await (await asyncio.sleep, await database query, etc.)
- **THEN** callback code awaits naturally within event task

### Requirement: Async Event Loop Integration
The system SHALL integrate properly with asyncio event loop.

#### Scenario: Background task for events
- **WHEN** user subscribes to events while event loop is running
- **THEN** system creates asyncio task to read stream (not thread)

#### Scenario: Cancellation support
- **WHEN** user cancels subscription or event loop is cancelled
- **THEN** event task is gracefully cancelled
