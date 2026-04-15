"""Tests for configuration and exception types."""

import pytest

from opencode_server_client.config import RetryConfig, ServerConfig
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


class TestServerConfig:
    """Test ServerConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating ServerConfig with minimal parameters."""
        config = ServerConfig(base_url="http://localhost:8000")

        assert config.base_url == "http://localhost:8000"
        assert config.basic_auth is None
        assert config.timeout == 30.0

    def test_creation_with_auth(self):
        """Test creating ServerConfig with basic auth."""
        config = ServerConfig(
            base_url="http://localhost:8000", basic_auth=("user", "pass")
        )

        assert config.base_url == "http://localhost:8000"
        assert config.basic_auth == ("user", "pass")

    def test_creation_with_custom_timeout(self):
        """Test creating ServerConfig with custom timeout."""
        config = ServerConfig(base_url="http://localhost:8000", timeout=60.0)

        assert config.timeout == 60.0

    def test_immutability(self):
        """Test that ServerConfig is immutable (frozen)."""
        config = ServerConfig(base_url="http://localhost:8000")

        with pytest.raises(AttributeError):
            config.base_url = "http://localhost:9000"


class TestRetryConfig:
    """Test RetryConfig dataclass."""

    def test_creation_with_defaults(self):
        """Test creating RetryConfig with default values."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0

    def test_creation_with_custom_values(self):
        """Test creating RetryConfig with custom values."""
        config = RetryConfig(
            max_retries=5, initial_delay=2.0, max_delay=60.0, exponential_base=1.5
        )

        assert config.max_retries == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 1.5

    def test_validation_exponential_base_must_be_greater_than_1(self):
        """Test that exponential_base must be > 1.0."""
        with pytest.raises(ValueError, match="exponential_base must be > 1.0"):
            RetryConfig(exponential_base=1.0)

    def test_validation_exponential_base_cannot_be_less_than_1(self):
        """Test that exponential_base cannot be <= 1.0."""
        with pytest.raises(ValueError, match="exponential_base must be > 1.0"):
            RetryConfig(exponential_base=0.5)

    def test_immutability(self):
        """Test that RetryConfig is immutable (frozen)."""
        config = RetryConfig()

        with pytest.raises(AttributeError):
            config.max_retries = 5


class TestExceptionHierarchy:
    """Test exception hierarchy and behavior."""

    def test_base_exception_is_exception(self):
        """Test that OpencodeError inherits from Exception."""
        assert issubclass(OpencodeError, Exception)

    def test_session_error_inheritance(self):
        """Test that SessionError inherits from OpencodeError."""
        assert issubclass(SessionError, OpencodeError)

    def test_session_creation_error_inheritance(self):
        """Test that SessionCreationError inherits from SessionError."""
        assert issubclass(SessionCreationError, SessionError)

    def test_session_not_found_error_inheritance(self):
        """Test that SessionNotFoundError inherits from SessionError."""
        assert issubclass(SessionNotFoundError, SessionError)

    def test_prompt_submission_error_inheritance(self):
        """Test that PromptSubmissionError inherits from OpencodeError."""
        assert issubclass(PromptSubmissionError, OpencodeError)

    def test_worktree_error_inheritance(self):
        """Test that WorktreeError inherits from OpencodeError."""
        assert issubclass(WorktreeError, OpencodeError)

    def test_event_stream_error_inheritance(self):
        """Test that EventStreamError inherits from OpencodeError."""
        assert issubclass(EventStreamError, OpencodeError)

    def test_retry_exhausted_error_inheritance(self):
        """Test that RetryExhaustedError inherits from OpencodeError."""
        assert issubclass(RetryExhaustedError, OpencodeError)

    def test_raising_base_exception(self):
        """Test raising OpencodeError."""
        with pytest.raises(OpencodeError):
            raise OpencodeError("An error occurred")

    def test_raising_session_creation_error(self):
        """Test raising SessionCreationError."""
        with pytest.raises(SessionCreationError):
            raise SessionCreationError("Could not create session")

    def test_raising_retry_exhausted_error(self):
        """Test raising RetryExhaustedError."""
        with pytest.raises(RetryExhaustedError):
            raise RetryExhaustedError("All retries exhausted")

    def test_exception_catching(self):
        """Test that specific errors can be caught as base types."""
        try:
            raise SessionCreationError("Test")
        except OpencodeError:
            pass  # Should be caught
        except Exception:
            pytest.fail("Should have been caught as OpencodeError")
