"""Tests for exception hierarchy and behavior."""

import pytest

from opencode_server_client.exceptions import (
    EventStreamError,
    OpencodeError,
    PromptSubmissionError,
    RetryExhaustedError,
    SessionCreationError,
    SessionError,
    SessionNotFoundError,
    WorktreeError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_opencode_error_is_base_exception(self):
        """Test that OpencodeError is the base exception."""
        assert issubclass(OpencodeError, Exception)

    def test_session_error_inherits_from_opencode_error(self):
        """Test that SessionError inherits from OpencodeError."""
        assert issubclass(SessionError, OpencodeError)

    def test_session_creation_error_inherits_from_session_error(self):
        """Test that SessionCreationError inherits from SessionError."""
        assert issubclass(SessionCreationError, SessionError)

    def test_session_not_found_error_inherits_from_session_error(self):
        """Test that SessionNotFoundError inherits from SessionError."""
        assert issubclass(SessionNotFoundError, SessionError)

    def test_prompt_submission_error_inherits_from_opencode_error(self):
        """Test that PromptSubmissionError inherits from OpencodeError."""
        assert issubclass(PromptSubmissionError, OpencodeError)

    def test_worktree_error_inherits_from_opencode_error(self):
        """Test that WorktreeError inherits from OpencodeError."""
        assert issubclass(WorktreeError, OpencodeError)

    def test_event_stream_error_inherits_from_opencode_error(self):
        """Test that EventStreamError inherits from OpencodeError."""
        assert issubclass(EventStreamError, OpencodeError)

    def test_retry_exhausted_error_inherits_from_opencode_error(self):
        """Test that RetryExhaustedError inherits from OpencodeError."""
        assert issubclass(RetryExhaustedError, OpencodeError)


class TestRaisingExceptions:
    """Test raising and catching exceptions."""

    def test_raise_opencode_error(self):
        """Test raising OpencodeError."""
        with pytest.raises(OpencodeError):
            raise OpencodeError("Test error")

    def test_raise_session_error(self):
        """Test raising SessionError."""
        with pytest.raises(SessionError):
            raise SessionError("Session error")

    def test_raise_session_creation_error(self):
        """Test raising SessionCreationError."""
        with pytest.raises(SessionCreationError):
            raise SessionCreationError("Could not create session")

    def test_raise_session_not_found_error(self):
        """Test raising SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError):
            raise SessionNotFoundError("Session not found")

    def test_raise_prompt_submission_error(self):
        """Test raising PromptSubmissionError."""
        with pytest.raises(PromptSubmissionError):
            raise PromptSubmissionError("Failed to submit prompt")

    def test_raise_worktree_error(self):
        """Test raising WorktreeError."""
        with pytest.raises(WorktreeError):
            raise WorktreeError("Worktree operation failed")

    def test_raise_event_stream_error(self):
        """Test raising EventStreamError."""
        with pytest.raises(EventStreamError):
            raise EventStreamError("Event stream disconnected")

    def test_raise_retry_exhausted_error(self):
        """Test raising RetryExhaustedError."""
        with pytest.raises(RetryExhaustedError):
            raise RetryExhaustedError("All retries exhausted")


class TestExceptionCatching:
    """Test catching exceptions at various levels."""

    def test_catch_session_creation_error_as_session_error(self):
        """Test catching SessionCreationError as SessionError."""
        try:
            raise SessionCreationError("Failed to create")
        except SessionError:
            pass  # Should catch
        except Exception:
            pytest.fail("Should have caught as SessionError")

    def test_catch_session_error_as_opencode_error(self):
        """Test catching SessionError as OpencodeError."""
        try:
            raise SessionError("Session error")
        except OpencodeError:
            pass  # Should catch
        except Exception:
            pytest.fail("Should have caught as OpencodeError")

    def test_catch_prompt_submission_error_as_opencode_error(self):
        """Test catching PromptSubmissionError as OpencodeError."""
        try:
            raise PromptSubmissionError("Failed")
        except OpencodeError:
            pass  # Should catch
        except Exception:
            pytest.fail("Should have caught as OpencodeError")

    def test_catch_specific_exceptions_in_order(self):
        """Test catching specific exceptions in priority order."""

        def raise_session_creation_error():
            raise SessionCreationError("Failed")

        try:
            raise_session_creation_error()
        except SessionCreationError:
            pass  # Specific exception caught first
        except SessionError:
            pytest.fail("Should have caught specific SessionCreationError first")

    def test_exception_message_preserved(self):
        """Test that exception message is preserved."""
        msg = "Custom error message"
        try:
            raise SessionCreationError(msg)
        except SessionCreationError as e:
            assert str(e) == msg

    def test_exception_chaining(self):
        """Test exception chaining with 'from'."""
        original_error = ValueError("Original error")
        try:
            try:
                raise original_error
            except ValueError as e:
                raise SessionCreationError("Failed to create") from e
        except SessionCreationError as e:
            assert e.__cause__ == original_error
