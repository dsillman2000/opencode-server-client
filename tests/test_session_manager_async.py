"""Tests for AsyncSessionManager - async CRUD operations on sessions."""

import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock

from opencode_server_client.session.async_manager import AsyncSessionManager


class TestAsyncSessionManager(TestCase):
    """Test AsyncSessionManager async CRUD operations."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.mock_http_client.post = AsyncMock()
        self.mock_http_client.get = AsyncMock()
        self.mock_http_client.delete = AsyncMock()
        self.mock_http_client.request = AsyncMock()
        self.manager = AsyncSessionManager(self.mock_http_client, default_directory="/default/dir")

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def test_create_minimal_params(self):
        """Test create() with minimal parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "abc123",
            "created_at": "2024-04-15T10:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.post.return_value = mock_response

        self.loop.run_until_complete(self.manager.create())

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session")

    def test_create_with_title_and_parent(self):
        """Test create() with title and parent_id."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "abc123",
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.post.return_value = mock_response

        self.loop.run_until_complete(self.manager.create(title="Test Session", parent_id="parent123"))

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("json", kwargs)
        self.assertEqual(kwargs["json"]["title"], "Test Session")
        self.assertEqual(kwargs["json"]["parent_id"], "parent123")

    def test_create_with_custom_directory(self):
        """Test create() with custom directory override."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "abc123",
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.post.return_value = mock_response

        self.loop.run_until_complete(self.manager.create(directory="/custom/dir"))

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs["directory"], "/custom/dir")

    def test_create_with_error(self):
        """Test create() handles errors gracefully."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("400 Bad Request")
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(Exception):
            self.loop.run_until_complete(self.manager.create())

    def test_list_returns_sessions(self):
        """Test list() returns session list."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"session_id": "abc123"},
            {"session_id": "xyz789"},
        ]
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.get.return_value = mock_response

        result = self.loop.run_until_complete(self.manager.list())

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["session_id"], "abc123")

    def test_list_with_empty_directory(self):
        """Test list() with empty directory."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.get.return_value = mock_response

        result = self.loop.run_until_complete(self.manager.list())

        self.assertEqual(result, [])

    def test_list_paginated_response(self):
        """Test list() handles paginated response format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sessions": [{"session_id": "abc123"}],
            "next_page_token": None,
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.get.return_value = mock_response

        result = self.loop.run_until_complete(self.manager.list())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], "abc123")

    def test_get_valid_session(self):
        """Test get() with valid session_id."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "abc123",
            "created_at": "2024-04-15T10:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.get.return_value = mock_response

        result = self.loop.run_until_complete(self.manager.get("abc123"))

        self.mock_http_client.get.assert_called_once()
        args, kwargs = self.mock_http_client.get.call_args
        self.assertEqual(args[0], "/session/abc123")
        self.assertEqual(result["session_id"], "abc123")

    def test_get_not_found(self):
        """Test get() with 404 error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        self.mock_http_client.get.return_value = mock_response

        with self.assertRaises(Exception):
            self.loop.run_until_complete(self.manager.get("nonexistent"))

    def test_update_succeeds(self):
        """Test update() can rename a session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "abc123",
            "title": "Example rename",
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.request.return_value = mock_response

        result = self.loop.run_until_complete(self.manager.update("abc123", title="Example rename"))

        self.mock_http_client.request.assert_called_once()
        args, kwargs = self.mock_http_client.request.call_args
        self.assertEqual(args[0], "PATCH")
        self.assertEqual(args[1], "/session/abc123")
        self.assertEqual(kwargs["json"], {"title": "Example rename"})
        self.assertEqual(result["title"], "Example rename")

    def test_update_requires_changes(self):
        """Test update() rejects empty patches."""
        with self.assertRaises(ValueError):
            self.loop.run_until_complete(self.manager.update("abc123"))

    def test_delete_succeeds(self):
        """Test delete() succeeds."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.delete.return_value = mock_response

        self.loop.run_until_complete(self.manager.delete("abc123"))

        self.mock_http_client.delete.assert_called_once()
        args, kwargs = self.mock_http_client.delete.call_args
        self.assertEqual(args[0], "/session/abc123")

    def test_delete_not_found(self):
        """Test delete() with 404 error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        self.mock_http_client.delete.return_value = mock_response

        with self.assertRaises(Exception):
            self.loop.run_until_complete(self.manager.delete("nonexistent"))

    def test_default_directory_override(self):
        """Test default directory can be overridden per operation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "abc123",
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_http_client.get.return_value = mock_response

        self.loop.run_until_complete(self.manager.get("abc123", directory="/override/dir"))

        args, kwargs = self.mock_http_client.get.call_args
        self.assertEqual(kwargs["directory"], "/override/dir")
