"""Integration tests for async workflows - end-to-end tests."""

import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from opencode_server_client.client_async import AsyncOpencodeServerClient
from opencode_server_client.config import ServerConfig


class TestAsyncWorkflowIntegration(TestCase):
    """Integration tests for async workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = ServerConfig(base_url="http://localhost:8000")

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def test_config_is_valid(self):
        """Test ServerConfig is valid."""
        self.assertEqual(self.config.base_url, "http://localhost:8000")

    def test_async_client_can_be_created(self):
        """Test async client can be instantiated."""
        client = AsyncOpencodeServerClient(self.config)
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.sessions)
        self.assertIsNotNone(client.prompts)
        self.assertIsNotNone(client.events)

    def test_async_client_has_required_methods(self):
        """Test async client has required methods."""
        methods = [
            "create_session",
            "list_all_sessions",
            "delete_session",
            "submit_prompt_and_wait",
            "close",
        ]
        client = AsyncOpencodeServerClient(self.config)
        for method in methods:
            self.assertTrue(hasattr(client, method))

    def test_async_sessions_manager_methods(self):
        """Test async sessions manager has required methods."""
        methods = ["create", "list", "get", "update", "delete"]
        client = AsyncOpencodeServerClient(self.config)
        for method in methods:
            self.assertTrue(hasattr(client.sessions, method))

    def test_async_prompts_manager_methods(self):
        """Test async prompts manager has required methods."""
        methods = ["submit_prompt", "abort_session"]
        client = AsyncOpencodeServerClient(self.config)
        for method in methods:
            self.assertTrue(hasattr(client.prompts, method))

    def test_async_events_manager_methods(self):
        """Test async events manager has required methods."""
        methods = ["subscribe", "unsubscribe", "close"]
        client = AsyncOpencodeServerClient(self.config)
        for method in methods:
            self.assertTrue(hasattr(client.events, method))

    def test_async_manager_supports_context_manager(self):
        """Test async managers support async context manager protocol."""
        client = AsyncOpencodeServerClient(self.config)

        async def check_aenter():
            return hasattr(client, "__aenter__") and hasattr(client, "__aexit__")

        result = self.loop.run_until_complete(check_aenter())
        self.assertTrue(result)
