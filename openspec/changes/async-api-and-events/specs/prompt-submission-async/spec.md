## ADDED Requirements

### Requirement: Async Submit Prompt
The system SHALL allow users to asynchronously submit prompts to sessions.

#### Scenario: Submit prompt with await
- **WHEN** user awaits `AsyncPromptSubmitter.submit_prompt(session_id="sess-123", prompt_text="...", model={...})`
- **THEN** coroutine POSTs to `/session/{id}/prompt_async` and returns message_id

#### Scenario: Submit with agent, system, tools
- **WHEN** user awaits `submit_prompt(..., agent="plan", system="...", tools={...})`
- **THEN** coroutine includes all fields in POST body

#### Scenario: Submit with abort=True
- **WHEN** user awaits `submit_prompt(..., abort=True)`
- **THEN** coroutine first POSTs to `/session/{id}/abort`, then POSTs prompt

#### Scenario: Submit with abort=False
- **WHEN** user awaits `submit_prompt(..., abort=False)`
- **THEN** coroutine skips abort call

#### Scenario: Submit with custom message_id
- **WHEN** user awaits `submit_prompt(..., message_id="msg-custom")`
- **THEN** coroutine uses provided message_id

#### Scenario: Submit with auto message_id
- **WHEN** user awaits `submit_prompt()` without message_id
- **THEN** coroutine generates UUID-based message_id

### Requirement: Async Abort Session
The system SHALL allow users to asynchronously abort sessions.

#### Scenario: Abort with await
- **WHEN** user awaits `AsyncPromptSubmitter.abort_session(session_id="sess-123")`
- **THEN** coroutine POSTs to `/session/{id}/abort` and returns True

#### Scenario: Abort non-existent session
- **WHEN** user awaits `abort_session(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised
