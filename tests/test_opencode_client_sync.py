"""Tests for OpencodeServerClient - main synchronous client."""

from unittest import TestCase
from unittest.mock import patch

from opencode_server_client.client_sync import OpencodeServerClient
from opencode_server_client.config import ServerConfig

# ruff: noqa F841


class TestOpencodeServerClient(TestCase):
    """Test OpencodeServerClient operations."""

    def setUp(self):
        """Set up client for tests."""
        self.config = ServerConfig(base_url="http://localhost:8000")

    def test_client_initialization_with_defaults(self):
        """Test client initialization with default parameters."""
        client = OpencodeServerClient(self.config)

        self.assertIsNotNone(client.sessions)
        self.assertIsNotNone(client.prompts)
        self.assertIsNotNone(client.events)

    def test_client_initialization_with_all_parameters(self):
        """Test client initialization with all parameters."""
        from opencode_server_client.config import RetryConfig

        retry_config = RetryConfig(max_retries=5)
        client = OpencodeServerClient(
            self.config,
            retry_config=retry_config,
            default_directory="/test/dir",
        )

        self.assertEqual(client.default_directory, "/test/dir")

    def test_manager_property_accessors(self):
        """Test manager property accessors."""
        client = OpencodeServerClient(self.config)

        # Accessors should return manager instances
        self.assertIsNotNone(client.sessions)
        self.assertIsNotNone(client.prompts)
        self.assertIsNotNone(client.events)

    @patch("opencode_server_client.session.sync_manager.SessionManager.create")
    def test_create_session_convenience_method(self, mock_create):
        """Test create_session() convenience method."""
        mock_create.return_value = {"session_id": "abc123"}

        client = OpencodeServerClient(self.config)
        result = client.create_session(title="Test Session")

        mock_create.assert_called_once()

    @patch("opencode_server_client.session.sync_manager.SessionManager.list")
    def test_list_all_sessions_convenience_method(self, mock_list):
        """Test list_all_sessions() convenience method."""
        mock_list.return_value = [{"session_id": "abc123"}]

        client = OpencodeServerClient(self.config)
        result = client.list_all_sessions()

        mock_list.assert_called_once()
        self.assertEqual(len(result), 1)

    @patch("opencode_server_client.session.sync_manager.SessionManager.delete")
    def test_delete_session_convenience_method(self, mock_delete):
        """Test delete_session() convenience method."""
        client = OpencodeServerClient(self.config)
        client.delete_session("abc123")

        mock_delete.assert_called_once_with("abc123", directory=None)

    @patch("opencode_server_client.session.sync_manager.SessionManager.update")
    def test_update_session_convenience_method(self, mock_update):
        """Test update_session() convenience method."""
        mock_update.return_value = {"session_id": "abc123", "title": "Example rename"}

        client = OpencodeServerClient(self.config)
        result = client.update_session("abc123", title="Example rename")

        mock_update.assert_called_once_with(
            "abc123",
            title="Example rename",
            parent_id=None,
            directory=None,
        )
        self.assertEqual(result["title"], "Example rename")

    def test_context_manager_support(self):
        """Test context manager support (with statement)."""
        with OpencodeServerClient(self.config) as client:
            self.assertIsNotNone(client.sessions)

    @patch("opencode_server_client.events.sync_subscriber.EventSubscriber.close")
    def test_cleanup_on_context_manager_exit(self, mock_close):
        """Test cleanup on context manager exit."""
        with OpencodeServerClient(self.config) as client:
            pass

        mock_close.assert_called_once()

    def test_submit_prompt_and_wait_basic(self):
        """Test submit_prompt_and_wait() basic workflow."""
        client = OpencodeServerClient(self.config)

        # Mock the managers
        with patch.object(client.prompts, "submit_prompt"):
            with patch.object(client.events, "subscribe") as mock_subscribe:
                # Simulate idle event immediately
                def trigger_callbacks(on_event=None, on_idle=None, **kwargs):
                    if on_idle:
                        from datetime import datetime

                        from opencode_server_client.events.types import SessionIdleEvent

                        on_idle(
                            SessionIdleEvent(
                                session_id="abc123",
                                timestamp=datetime.now(),
                            )
                        )

                mock_subscribe.side_effect = trigger_callbacks

                messages = client.submit_prompt_and_wait(
                    session_id="abc123",
                    text="Hello",
                    timeout=1.0,
                )

                # Should complete without timeout
                self.assertIsNotNone(messages)

    def test_submit_prompt_and_wait_timeout(self):
        """Test submit_prompt_and_wait() timeout handling."""
        client = OpencodeServerClient(self.config)

        with patch.object(client.prompts, "submit_prompt"):
            with patch.object(client.events, "subscribe"):
                # Don't trigger idle event, should timeout
                with self.assertRaises(TimeoutError):
                    client.submit_prompt_and_wait(
                        session_id="abc123",
                        text="Hello",
                        timeout=0.1,
                    )

    @patch("opencode_server_client.events.sync_subscriber.EventSubscriber.close")
    def test_close_method(self, mock_close):
        """Test close() method."""
        client = OpencodeServerClient(self.config)
        client.close()

        mock_close.assert_called_once()
