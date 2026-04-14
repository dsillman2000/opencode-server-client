## ADDED Requirements

### Requirement: Submit Prompt to Session
The system SHALL allow users to submit a prompt to a session for processing.

#### Scenario: Submit simple text prompt
- **WHEN** user calls `PromptSubmitter.submit_prompt(session_id="sess-123", prompt_text="What is 2+2?", model={providerID: "nvidia", modelID: "nim"})`
- **THEN** system POSTs to `/session/sess-123/prompt_async` with text part and returns message_id

#### Scenario: Prompt submission with custom agent
- **WHEN** user calls `submit_prompt(..., agent="plan")`
- **THEN** system includes agent in POST body

#### Scenario: Prompt submission with system prompt
- **WHEN** user calls `submit_prompt(..., system="You are a helpful assistant")`
- **THEN** system includes system prompt in POST body

#### Scenario: Prompt submission with tools enabled
- **WHEN** user calls `submit_prompt(..., tools={"bash": true, "read": false})`
- **THEN** system includes tool configuration in POST body

#### Scenario: Prompt submission generates message ID
- **WHEN** user calls `submit_prompt()` without message_id
- **THEN** system generates a unique message_id internally

#### Scenario: Prompt submission with custom message ID
- **WHEN** user calls `submit_prompt(..., message_id="msg-custom")`
- **THEN** system uses provided message_id in request

#### Scenario: Prompt submission retries on 502
- **WHEN** user submits prompt and server returns 502 then 204
- **THEN** system retries and returns message_id

### Requirement: Abort Before Submit
The system SHALL support atomically aborting ongoing work before submitting new prompt.

#### Scenario: Submit with abort flag true
- **WHEN** user calls `submit_prompt(..., abort=True)`
- **THEN** system first POSTs to `/session/sess-123/abort`, then immediately POSTs prompt to `/session/sess-123/prompt_async`

#### Scenario: Submit with abort flag false
- **WHEN** user calls `submit_prompt(..., abort=False)` or omits abort parameter
- **THEN** system skips abort call and only submits prompt

#### Scenario: Abort fails then submit succeeds
- **WHEN** user submits with abort=True and abort returns 502 then succeeds
- **THEN** system retries abort per retry logic, then proceeds with submit

#### Scenario: Abort succeeds then submit fails
- **WHEN** abort succeeds but submit returns 502
- **THEN** prompt submission is retried; session state is aborted (desired state achieved partially)

### Requirement: Abort Session
The system SHALL allow users to abort any ongoing work in a session.

#### Scenario: Abort session succeeds
- **WHEN** user calls `PromptSubmitter.abort_session(session_id="sess-123")`
- **THEN** system POSTs to `/session/sess-123/abort` and returns True

#### Scenario: Abort non-existent session
- **WHEN** user calls `abort_session(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised

#### Scenario: Abort session with directory context
- **WHEN** user calls `abort_session(..., directory="...")`
- **THEN** request includes `X-Opencode-Directory` header
