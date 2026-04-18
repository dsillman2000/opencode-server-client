# Response Tracking (Async) Specification

> **NOTE**: This is the async version of the response-tracking-sync specification.

## Purpose

Provides async versions of response tracking and polling operations for use with asyncio.

## ADDED Requirements

> **NOTE**: Part IDs are generated as 30-character base-62 monotonic identifiers prefixed with `prt_` (e.g., `prt_abc123def456ghijklmnopqr`). This matches OpenCode's native ID semantics using timestamp-derived ordering.

### Requirement: Async Get Messages
The system SHALL allow users to asynchronously retrieve messages from a session.

#### Scenario: Get messages with await
- **WHEN** user awaits `AsyncResponsePoller.get_messages(session_id="sess-123")`
- **THEN** coroutine GETs `/session/{id}/message` and returns `List[Message]`

#### Scenario: Get empty message list
- **WHEN** user awaits `get_messages()` for new session
- **THEN** coroutine returns empty list

#### Scenario: Get messages with directory context
- **WHEN** user awaits `get_messages(..., directory="...")`
- **THEN** request includes `X-Opencode-Directory` header

### Requirement: Async Get Message Detail
The system SHALL allow users to asynchronously retrieve full message details.

#### Scenario: Get message detail with await
- **WHEN** user awaits `AsyncResponsePoller.get_message_detail(session_id="sess-123", message_id="msg-456")`
- **THEN** coroutine GETs `/session/{id}/message/{messageID}` and returns {info: Message, parts: List[Part]}

#### Scenario: Get detail for non-existent message
- **WHEN** user awaits `get_message_detail()` with invalid message_id and server responds 404
- **THEN** `SessionNotFoundError` is raised

### Requirement: Async Wait for Idle
The system SHALL allow users to asynchronously wait for session completion.

#### Scenario: Wait for idle with await
- **WHEN** user awaits `AsyncResponsePoller.wait_for_idle(session_id="sess-123", timeout=300, poll_interval=0.5)`
- **THEN** coroutine polls until idle or timeout, uses `await asyncio.sleep()` between polls, returns True/False

#### Scenario: Wait for idle timeout
- **WHEN** user awaits with timeout=5 and session takes 10 seconds
- **THEN** coroutine returns False (timeout)

### Requirement: Async Submit and Wait
The system SHALL provide convenient async method combining submission and polling.

#### Scenario: Submit and wait with await
- **WHEN** user awaits `AsyncOpencodeServerClient.submit_prompt_and_wait(session_id="...", prompt_text="...", model={...}, timeout=300)`
- **THEN** coroutine submits prompt, polls asynchronously until idle or timeout, returns (True, messages_list)

#### Scenario: Submit and wait times out
- **WHEN** user awaits with timeout=5 and processing takes longer
- **THEN** coroutine returns (False, current_messages_list)

#### Scenario: Submit and wait with abort
- **WHEN** user awaits `submit_prompt_and_wait(..., abort=True)`
- **THEN** coroutine aborts first, then submits, then waits