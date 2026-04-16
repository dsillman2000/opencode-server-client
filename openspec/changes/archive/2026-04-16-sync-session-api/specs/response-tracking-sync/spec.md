## ADDED Requirements

### Requirement: Fetch Messages from Session
The system SHALL allow users to retrieve all messages in a session.

#### Scenario: Get all messages
- **WHEN** user calls `ResponsePoller.get_messages(session_id="sess-123")`
- **THEN** system GETs `/session/sess-123/message` and returns `List[Message]`

#### Scenario: Messages list is empty initially
- **WHEN** user creates new session and immediately gets messages
- **THEN** system returns empty list

#### Scenario: Messages include user and assistant
- **WHEN** user submits prompt and gets messages
- **THEN** returned list contains both UserMessage and AssistantMessage objects

#### Scenario: Get messages with directory context
- **WHEN** user calls `get_messages(..., directory="...")`
- **THEN** request includes `X-Opencode-Directory` header

#### Scenario: Get messages retries on 502
- **WHEN** user gets messages and server returns 502 then 200 with messages
- **THEN** system retries and returns message list

#### Scenario: Session not found
- **WHEN** user calls `get_messages(session_id="invalid")` and server responds 404
- **THEN** `SessionNotFoundError` is raised

### Requirement: Get Message Detail
The system SHALL allow users to retrieve full details of a specific message including parts.

#### Scenario: Get message by ID
- **WHEN** user calls `ResponsePoller.get_message_detail(session_id="sess-123", message_id="msg-456")`
- **THEN** system GETs `/session/sess-123/message/msg-456` and returns {info: Message, parts: List[Part]}

#### Scenario: Message detail includes all parts
- **WHEN** message has text parts, tool parts, reasoning parts
- **THEN** returned parts list includes all of them in order

#### Scenario: Message not found
- **WHEN** user calls `get_message_detail()` for non-existent message_id and server responds 404
- **THEN** `SessionNotFoundError` is raised

### Requirement: Combined Submit and Wait
The system SHALL provide convenient method combining prompt submission with completion polling.

#### Scenario: Submit and wait succeeds
- **WHEN** user calls `OpencodeServerClient.submit_prompt_and_wait(session_id="...", prompt_text="...", model={...}, timeout=300)`
- **THEN** system submits prompt, polls until idle or timeout, returns (True, messages_list)

#### Scenario: Submit and wait times out
- **WHEN** user calls with timeout=5 and session takes 10 seconds
- **THEN** returns (False, current_messages_list) - success=False indicates timeout

#### Scenario: Submit and wait with abort
- **WHEN** user calls `submit_prompt_and_wait(..., abort=True)`
- **THEN** system aborts first, then submits, then waits

#### Scenario: Submit and wait with custom poll interval
- **WHEN** user calls `submit_prompt_and_wait(..., poll_interval=0.1)`
- **THEN** polling checks status every 0.1 seconds for responsiveness
