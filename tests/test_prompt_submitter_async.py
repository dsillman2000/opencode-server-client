"""Tests for AsyncPromptSubmitter - async prompt submission."""

import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock

from opencode_server_client.prompt.async_submitter import AsyncPromptSubmitter


class TestAsyncPromptSubmitter(TestCase):
    """Test AsyncPromptSubmitter async operations."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.mock_http_client.post = AsyncMock()
        self.submitter = AsyncPromptSubmitter(self.mock_http_client)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def test_submit_prompt_text_only(self):
        """Test submit_prompt() with text only."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        result = self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123", text="What is the file structure?"
            )
        )

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session/abc123/prompt_async")
        self.assertIn("json", kwargs)
        payload = kwargs["json"]
        self.assertIn("parts", payload)
        self.assertIn("messageID", payload)
        self.assertIsNotNone(result)

    def test_submit_prompt_with_agent(self):
        """Test submit_prompt() with agent parameter."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(session_id="abc123", text="Test", agent="plan")
        )

        args, kwargs = self.mock_http_client.post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload.get("agent"), "plan")

    def test_submit_prompt_with_system_prompt(self):
        """Test submit_prompt() with system prompt."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123",
                text="Test",
                system_prompt="You are a helpful assistant.",
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload.get("system_prompt"), "You are a helpful assistant.")

    def test_submit_prompt_with_tools_config(self):
        """Test submit_prompt() with tools config."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()
        tools_config = {"enabled": True, "allowed_tools": ["read", "write"]}

        self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123", text="Test", tools=tools_config
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload.get("tools"), tools_config)

    def test_submit_prompt_auto_generates_message_id(self):
        """Test submit_prompt() auto-generates message_id."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(session_id="abc123", text="Test")
        )

        args, kwargs = self.mock_http_client.post.call_args
        payload = kwargs["json"]
        self.assertIn("messageID", payload)
        self.assertIsNotNone(payload["messageID"])

    def test_submit_prompt_with_custom_message_id(self):
        """Test submit_prompt() with custom message_id."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        result = self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123", text="Test", message_id="msg-custom-123"
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        payload = kwargs["json"]
        self.assertEqual(payload["messageID"], "msg-custom-123")
        self.assertEqual(result, "msg-custom-123")

    def test_submit_prompt_with_abort_false(self):
        """Test submit_prompt() with abort=False (no abort call)."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(session_id="abc123", text="Test", abort=False)
        )

        self.mock_http_client.post.assert_called_once()

    def test_submit_prompt_with_abort_true(self):
        """Test submit_prompt() with abort=True (abort then submit)."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(session_id="abc123", text="Test", abort=True)
        )

        self.assertEqual(self.mock_http_client.post.call_count, 2)

    def test_abort_session_succeeds(self):
        """Test abort_session() succeeds."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(self.submitter.abort_session(session_id="abc123"))

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session/abc123/abort")

    def test_abort_session_not_found(self):
        """Test abort_session() with 404 error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        self.mock_http_client.post.return_value = mock_response

        with self.assertRaises(Exception):
            self.loop.run_until_complete(
                self.submitter.abort_session(session_id="nonexistent")
            )

    def test_submit_prompt_with_directory_context(self):
        """Test submit_prompt() includes directory context."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123",
                text="Hello",
                directory="/custom/dir",
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs.get("directory"), "/custom/dir")

    def test_submit_prompt_with_provider_and_model_id(self):
        """Test submit_prompt() with provider_id and model_id."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123",
                text="Hello",
                provider_id="nvidia",
                model_id="nim",
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("model", kwargs["json"])
        self.assertEqual(kwargs["json"]["model"]["providerID"], "nvidia")
        self.assertEqual(kwargs["json"]["model"]["modelID"], "nim")

    def test_submit_prompt_with_provider_id_only(self):
        """Test submit_prompt() with provider_id only."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123",
                text="Hello",
                provider_id="openai",
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("model", kwargs["json"])
        self.assertEqual(kwargs["json"]["model"]["providerID"], "openai")
        self.assertNotIn("modelID", kwargs["json"]["model"])

    def test_submit_prompt_with_model_id_only(self):
        """Test submit_prompt() with model_id only."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.submit_prompt(
                session_id="abc123",
                text="Hello",
                model_id="gpt-4",
            )
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("model", kwargs["json"])
        self.assertEqual(kwargs["json"]["model"]["modelID"], "gpt-4")
        self.assertNotIn("providerID", kwargs["json"]["model"])

    def test_abort_session_with_directory(self):
        """Test abort_session() with directory parameter."""
        self.mock_http_client.post.return_value.raise_for_status = MagicMock()

        self.loop.run_until_complete(
            self.submitter.abort_session(session_id="abc123", directory="/test/dir")
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session/abc123/abort")
        self.assertEqual(kwargs.get("directory"), "/test/dir")
