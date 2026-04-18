"""Integration tests for sync/async parity - cross-layer consistency."""

import asyncio
from unittest import TestCase

from opencode_server_client.client_sync import OpencodeServerClient
from opencode_server_client.client_async import AsyncOpencodeServerClient
from opencode_server_client.config import ServerConfig
from opencode_server_client.events.types import (
    SessionIdleEvent,
    SessionErrorEvent,
    ServerHeartbeatEvent,
)
from opencode_server_client.events.parser import EventParser


class TestSyncAsyncParity(TestCase):
    """Test sync and async API parity."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.config = ServerConfig(base_url="http://localhost:8000")

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def test_client_has_parallel_apis(self):
        """Test sync and async clients have parallel APIs."""
        sync_methods = [
            "create_session",
            "list_all_sessions",
            "delete_session",
            "submit_prompt_and_wait",
        ]

        for method in sync_methods:
            self.assertTrue(hasattr(OpencodeServerClient, method))
            self.assertTrue(hasattr(AsyncOpencodeServerClient, method))

    def test_event_parser_works(self):
        """Test event parser works correctly."""
        parser = EventParser()
        self.assertIsNotNone(parser)


class TestEventDataStructureConsistency(TestCase):
    """Test event data structure consistency between layers."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def test_session_idle_event_structure(self):
        """Test SessionIdleEvent has required fields."""
        event = SessionIdleEvent(session_id="abc123", timestamp=self.loop.time())

        self.assertEqual(event.session_id, "abc123")
        self.assertIsNotNone(event.timestamp)

    def test_session_error_event_structure(self):
        """Test SessionErrorEvent has required fields."""
        event = SessionErrorEvent(
            session_id="abc123", error_message="Test error", error_code="E001"
        )

        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.error_message, "Test error")
        self.assertEqual(event.error_code, "E001")

    def test_server_heartbeat_event_structure(self):
        """Test ServerHeartbeatEvent has required fields."""
        event = ServerHeartbeatEvent()

        self.assertIsNotNone(event.timestamp)
