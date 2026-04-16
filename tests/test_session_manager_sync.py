"""Tests for SessionManager - CRUD operations on sessions."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from opencode_server_client.session.sync_manager import SessionManager


class TestSessionManager(TestCase):
    """Test SessionManager CRUD operations."""

    def setUp(self):
        """Set up mock HTTP client for tests."""
        self.mock_http_client = MagicMock()
        self.manager = SessionManager(
            self.mock_http_client, default_directory="/default/dir"
        )

    def test_create_minimal_params(self):
        """Test create() with minimal parameters."""
        self.mock_http_client.post.return_value.json.return_value = {
            "session_id": "abc123",
            "created_at": "2024-04-15T10:00:00Z",
        }

        result = self.manager.create()

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session")
        self.assertEqual(kwargs["directory"], "/default/dir")

    def test_create_with_title_and_parent(self):
        """Test create() with title and parent_id."""
        self.mock_http_client.post.return_value.json.return_value = {
            "session_id": "abc123",
        }

        result = self.manager.create(title="Test Session", parent_id="parent123")

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("json", kwargs)
        self.assertEqual(kwargs["json"]["title"], "Test Session")
        self.assertEqual(kwargs["json"]["parent_id"], "parent123")

    def test_create_with_custom_directory(self):
        """Test create() with custom directory override."""
        self.mock_http_client.post.return_value.json.return_value = {
            "session_id": "abc123",
        }

        result = self.manager.create(directory="/custom/dir")

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs["directory"], "/custom/dir")

    def test_create_with_error(self):
        """Test create() handles errors gracefully."""
        self.mock_http_client.post.return_value.raise_for_status.side_effect = (
            Exception("400 Bad Request")
        )

        with self.assertRaises(Exception):
            self.manager.create()

    def test_list_returns_sessions(self):
        """Test list() returns session list."""
        self.mock_http_client.get.return_value.json.return_value = [
            {"session_id": "abc123"},
            {"session_id": "xyz789"},
        ]

        result = self.manager.list()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["session_id"], "abc123")

    def test_list_with_empty_directory(self):
        """Test list() with empty directory."""
        self.mock_http_client.get.return_value.json.return_value = []

        result = self.manager.list()

        self.assertEqual(result, [])

    def test_list_paginated_response(self):
        """Test list() handles paginated response format."""
        self.mock_http_client.get.return_value.json.return_value = {
            "sessions": [{"session_id": "abc123"}],
            "next_page_token": None,
        }

        result = self.manager.list()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["session_id"], "abc123")

    def test_get_valid_session(self):
        """Test get() with valid session_id."""
        self.mock_http_client.get.return_value.json.return_value = {
            "session_id": "abc123",
            "created_at": "2024-04-15T10:00:00Z",
        }

        result = self.manager.get("abc123")

        self.mock_http_client.get.assert_called_once()
        args, kwargs = self.mock_http_client.get.call_args
        self.assertEqual(args[0], "/session/abc123")
        self.assertEqual(result["session_id"], "abc123")

    def test_get_not_found(self):
        """Test get() with 404 error."""
        self.mock_http_client.get.return_value.raise_for_status.side_effect = Exception(
            "404 Not Found"
        )

        with self.assertRaises(Exception):
            self.manager.get("nonexistent")

    def test_delete_succeeds(self):
        """Test delete() succeeds."""
        self.mock_http_client.delete.return_value.json.return_value = {}

        self.manager.delete("abc123")

        self.mock_http_client.delete.assert_called_once()
        args, kwargs = self.mock_http_client.delete.call_args
        self.assertEqual(args[0], "/session/abc123")

    def test_delete_not_found(self):
        """Test delete() with 404 error."""
        self.mock_http_client.delete.return_value.raise_for_status.side_effect = (
            Exception("404 Not Found")
        )

        with self.assertRaises(Exception):
            self.manager.delete("nonexistent")

    def test_default_directory_override(self):
        """Test default directory can be overridden per operation."""
        self.mock_http_client.get.return_value.json.return_value = {
            "session_id": "abc123",
        }

        self.manager.get("abc123", directory="/override/dir")

        args, kwargs = self.mock_http_client.get.call_args
        self.assertEqual(kwargs["directory"], "/override/dir")
