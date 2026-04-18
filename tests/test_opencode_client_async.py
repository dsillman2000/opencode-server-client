"""Tests for AsyncOpencodeServerClient - main async client interface."""

import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from opencode_server_client.client_async import AsyncOpencodeServerClient
from opencode_server_client.config import ServerConfig, RetryConfig


class TestAsyncOpencodeServerClient(TestCase):
    """Test AsyncOpencodeServerClient async operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = ServerConfig(base_url="http://localhost:8000")
        self.retry_config = RetryConfig(max_retries=3)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def test_async_client_initialization_defaults(self):
        """Test async client initialization with defaults."""
        with patch("opencode_server_client.client_async.AsyncHttpClient"):
            client = AsyncOpencodeServerClient(self.config)
            self.assertEqual(client.server_config, self.config)
            self.assertIsNone(client.default_directory)

    def test_async_client_initialization_with_params(self):
        """Test async client initialization with all parameters."""
        with patch("opencode_server_client.client_async.AsyncHttpClient"):
            client = AsyncOpencodeServerClient(
                self.config,
                retry_config=self.retry_config,
                default_directory="/test/dir",
            )
            self.assertEqual(client.retry_config, self.retry_config)
            self.assertEqual(client.default_directory, "/test/dir")

    def test_async_manager_property_accessors(self):
        """Test async manager property accessors."""
        with patch("opencode_server_client.client_async.AsyncHttpClient"):
            client = AsyncOpencodeServerClient(self.config)
            self.assertIsNotNone(client.sessions)
            self.assertIsNotNone(client.prompts)
            self.assertIsNotNone(client.events)
            self.assertIsNotNone(client.providers)

    @patch("opencode_server_client.client_async.AsyncHttpClient")
    def test_create_session_delegates(self, mock_http_client_cls):
        """Test create_session() delegates to sessions.create()."""
        mock_http_client = MagicMock()
        mock_http_client_cls.return_value = mock_http_client

        mock_sessions = MagicMock()
        mock_sessions.create = AsyncMock(return_value={"session_id": "abc123"})

        mock_prompts = MagicMock()
        mock_events = MagicMock()

        client = AsyncOpencodeServerClient.__new__(AsyncOpencodeServerClient)
        client.server_config = self.config
        client.retry_config = self.retry_config
        client.default_directory = None
        client._http_client = mock_http_client
        client.sessions = mock_sessions
        client.prompts = mock_prompts
        client.events = mock_events

        result = self.loop.run_until_complete(client.create_session(title="Test"))

        mock_sessions.create.assert_called_once_with(
            title="Test", parent_id=None, directory=None
        )
        self.assertEqual(result["session_id"], "abc123")

    @patch("opencode_server_client.client_async.AsyncHttpClient")
    def test_list_all_sessions_delegates(self, mock_http_client_cls):
        """Test list_all_sessions() delegates to sessions.list()."""
        mock_http_client = MagicMock()
        mock_http_client_cls.return_value = mock_http_client

        mock_sessions = MagicMock()
        mock_sessions.list = AsyncMock(return_value=[{"session_id": "abc123"}])

        mock_prompts = MagicMock()
        mock_events = MagicMock()

        client = AsyncOpencodeServerClient.__new__(AsyncOpencodeServerClient)
        client.server_config = self.config
        client.retry_config = self.retry_config
        client.default_directory = None
        client._http_client = mock_http_client
        client.sessions = mock_sessions
        client.prompts = mock_prompts
        client.events = mock_events

        result = self.loop.run_until_complete(client.list_all_sessions())

        mock_sessions.list.assert_called_once_with(directory=None)
        self.assertEqual(len(result), 1)

    @patch("opencode_server_client.client_async.AsyncHttpClient")
    def test_delete_session_delegates(self, mock_http_client_cls):
        """Test delete_session() delegates to sessions.delete()."""
        mock_http_client = MagicMock()
        mock_http_client_cls.return_value = mock_http_client

        mock_sessions = MagicMock()
        mock_sessions.delete = AsyncMock()

        mock_prompts = MagicMock()
        mock_events = MagicMock()

        client = AsyncOpencodeServerClient.__new__(AsyncOpencodeServerClient)
        client.server_config = self.config
        client.retry_config = self.retry_config
        client.default_directory = None
        client._http_client = mock_http_client
        client.sessions = mock_sessions
        client.prompts = mock_prompts
        client.events = mock_events

        self.loop.run_until_complete(client.delete_session("abc123"))

        mock_sessions.delete.assert_called_once_with("abc123", directory=None)


class TestAsyncOpencodeServerClientContextManager(TestCase):
    """Test AsyncOpencodeServerClient context manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = ServerConfig(base_url="http://localhost:8000")

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    @patch("opencode_server_client.client_async.AsyncHttpClient")
    def test_async_context_manager_support(self, mock_http_client_cls):
        """Test async context manager support."""
        mock_http_client = MagicMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)
        mock_http_client_cls.return_value = mock_http_client

        async def test_context():
            async with AsyncOpencodeServerClient(self.config) as client:
                self.assertIsNotNone(client)

        self.loop.run_until_complete(test_context())
        mock_http_client.__aenter__.assert_called_once()
        mock_http_client.__aexit__.assert_called_once_with(None, None, None)


class TestAsyncOpencodeServerClientConvenienceMethods(TestCase):
    """Test AsyncOpencodeServerClient convenience methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = ServerConfig(base_url="http://localhost:8000")

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    @patch("opencode_server_client.client_async.AsyncHttpClient")
    @patch("opencode_server_client.client_async.AsyncEventSubscriber")
    @patch("opencode_server_client.client_async.AsyncPromptSubmitter")
    @patch("opencode_server_client.client_async.AsyncSessionManager")
    def test_submit_prompt_and_wait(
        self, mock_sessions_cls, mock_prompts_cls, mock_events_cls, mock_http_client_cls
    ):
        """Test submit_prompt_and_wait() succeeds."""
        mock_http_client = MagicMock()
        mock_http_client_cls.return_value = mock_http_client

        mock_sessions = AsyncMock()
        mock_sessions.create = AsyncMock(return_value={"session_id": "abc123"})

        mock_prompts = AsyncMock()
        mock_prompts.submit_prompt = AsyncMock(return_value="msg-123")

        mock_events = AsyncMock()
        mock_events.subscribe = AsyncMock()

        client = AsyncOpencodeServerClient.__new__(AsyncOpencodeServerClient)
        client.server_config = self.config
        client.retry_config = RetryConfig()
        client.default_directory = None
        client._http_client = mock_http_client
        client.sessions = mock_sessions
        client.prompts = mock_prompts
        client.events = mock_events

        # Need to set up the idle event for wait
        with patch.object(asyncio, "Event") as mock_event_cls:
            mock_event = MagicMock()
            mock_event.is_set = MagicMock(side_effect=[False, True])
            mock_event_cls.return_value = mock_event

            self.loop.run_until_complete(
                client.submit_prompt_and_wait(session_id="abc123", text="Test prompt")
            )

    @patch("opencode_server_client.client_async.AsyncHttpClient")
    @patch("opencode_server_client.client_async.AsyncEventSubscriber")
    @patch("opencode_server_client.client_async.AsyncPromptSubmitter")
    @patch("opencode_server_client.client_async.AsyncSessionManager")
    def test_submit_prompt_and_wait_timeout(
        self, mock_sessions_cls, mock_prompts_cls, mock_events_cls, mock_http_client_cls
    ):
        """Test submit_prompt_and_wait() times out."""
        mock_http_client = MagicMock()
        mock_http_client_cls.return_value = mock_http_client

        mock_sessions = AsyncMock()
        mock_prompts = AsyncMock()
        mock_events = AsyncMock()
        mock_events.subscribe = AsyncMock()

        client = AsyncOpencodeServerClient.__new__(AsyncOpencodeServerClient)
        client.server_config = self.config
        client.retry_config = RetryConfig()
        client.default_directory = None
        client._http_client = mock_http_client
        client.sessions = mock_sessions
        client.prompts = mock_prompts
        client.events = mock_events

        # Mock Event to always return not set (simulates timeout)
        with patch.object(asyncio, "Event") as mock_event_cls:
            mock_event = MagicMock()
            mock_event.is_set = MagicMock(return_value=False)
            mock_event_cls.return_value = mock_event

            with self.assertRaises(TimeoutError):
                self.loop.run_until_complete(
                    client.submit_prompt_and_wait(
                        session_id="abc123", text="Test prompt", timeout=0.1
                    )
                )
