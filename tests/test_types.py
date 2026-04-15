"""Tests for type definitions."""

from datetime import datetime

from opencode_server_client.types import (
    AssistantMessage,
    MessageUpdatedEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionMetadata,
    SessionStatusEvent,
    UserMessage,
    WorktreeMetadata,
)


class TestSessionMetadata:
    """Test SessionMetadata dataclass."""

    def test_creation(self):
        """Test creating SessionMetadata."""
        now = datetime.now()
        metadata = SessionMetadata(
            session_id="sess-123",
            created_at=now,
            last_activity=now,
            workdir="/home/user/project",
        )

        assert metadata.session_id == "sess-123"
        assert metadata.created_at == now
        assert metadata.last_activity == now
        assert metadata.workdir == "/home/user/project"


class TestUserMessage:
    """Test UserMessage dataclass."""

    def test_creation_with_message_id(self):
        """Test creating UserMessage with explicit message_id."""
        now = datetime.now()
        msg = UserMessage(
            content="Hello, assistant!", timestamp=now, message_id="msg-123"
        )

        assert msg.content == "Hello, assistant!"
        assert msg.timestamp == now
        assert msg.message_id == "msg-123"

    def test_creation_without_message_id(self):
        """Test creating UserMessage without message_id."""
        now = datetime.now()
        msg = UserMessage(content="Hello, assistant!", timestamp=now)

        assert msg.content == "Hello, assistant!"
        assert msg.message_id is None


class TestAssistantMessage:
    """Test AssistantMessage dataclass."""

    def test_creation_with_message_id(self):
        """Test creating AssistantMessage with explicit message_id."""
        now = datetime.now()
        msg = AssistantMessage(
            content="Hello, user!", timestamp=now, message_id="msg-456"
        )

        assert msg.content == "Hello, user!"
        assert msg.timestamp == now
        assert msg.message_id == "msg-456"

    def test_creation_without_message_id(self):
        """Test creating AssistantMessage without message_id."""
        now = datetime.now()
        msg = AssistantMessage(content="Hello, user!", timestamp=now)

        assert msg.content == "Hello, user!"
        assert msg.message_id is None


class TestWorktreeMetadata:
    """Test WorktreeMetadata dataclass."""

    def test_creation_complete(self):
        """Test creating WorktreeMetadata with all fields."""
        metadata = WorktreeMetadata(
            path="/home/user/project",
            name="my-project",
            git_repo=True,
            python_version="3.10",
        )

        assert metadata.path == "/home/user/project"
        assert metadata.name == "my-project"
        assert metadata.git_repo is True
        assert metadata.python_version == "3.10"

    def test_creation_without_python_version(self):
        """Test creating WorktreeMetadata without python_version."""
        metadata = WorktreeMetadata(
            path="/home/user/project", name="my-project", git_repo=False
        )

        assert metadata.python_version is None


class TestSessionStatusEvent:
    """Test SessionStatusEvent dataclass."""

    def test_creation(self):
        """Test creating SessionStatusEvent."""
        now = datetime.now()
        event = SessionStatusEvent(session_id="sess-123", status="busy", timestamp=now)

        assert event.session_id == "sess-123"
        assert event.status == "busy"
        assert event.timestamp == now

    def test_status_values(self):
        """Test all valid status values."""
        now = datetime.now()

        for status in ["idle", "busy", "retry"]:
            event = SessionStatusEvent(
                session_id="sess-123", status=status, timestamp=now
            )
            assert event.status == status


class TestSessionIdleEvent:
    """Test SessionIdleEvent dataclass."""

    def test_creation(self):
        """Test creating SessionIdleEvent."""
        now = datetime.now()
        event = SessionIdleEvent(session_id="sess-123", timestamp=now)

        assert event.session_id == "sess-123"
        assert event.timestamp == now


class TestMessageUpdatedEvent:
    """Test MessageUpdatedEvent dataclass."""

    def test_creation(self):
        """Test creating MessageUpdatedEvent."""
        now = datetime.now()
        event = MessageUpdatedEvent(
            session_id="sess-123",
            message_id="msg-456",
            content="Updated message content",
            timestamp=now,
        )

        assert event.session_id == "sess-123"
        assert event.message_id == "msg-456"
        assert event.content == "Updated message content"
        assert event.timestamp == now


class TestSessionErrorEvent:
    """Test SessionErrorEvent dataclass."""

    def test_creation_with_error_code(self):
        """Test creating SessionErrorEvent with error code."""
        now = datetime.now()
        event = SessionErrorEvent(
            session_id="sess-123",
            error_message="An error occurred",
            error_code="ERR_001",
            timestamp=now,
        )

        assert event.session_id == "sess-123"
        assert event.error_message == "An error occurred"
        assert event.error_code == "ERR_001"
        assert event.timestamp == now

    def test_creation_without_error_code(self):
        """Test creating SessionErrorEvent without error code."""
        now = datetime.now()
        event = SessionErrorEvent(
            session_id="sess-123", error_message="An error occurred", timestamp=now
        )

        assert event.error_code is None

    def test_creation_with_default_timestamp(self):
        """Test creating SessionErrorEvent with default timestamp."""
        event = SessionErrorEvent(
            session_id="sess-123", error_message="An error occurred"
        )

        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
