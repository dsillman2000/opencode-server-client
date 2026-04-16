"""Tests for PromptSubmitter - submitting prompts and managing abortion."""

from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from opencode_server_client.prompt.sync_submitter import PromptSubmitter


class TestPromptSubmitter(TestCase):
    """Test PromptSubmitter operations."""

    def setUp(self):
        """Set up mock HTTP client for tests."""
        self.mock_http_client = MagicMock()
        self.submitter = PromptSubmitter(self.mock_http_client)

    def test_submit_prompt_text_only(self):
        """Test submit_prompt() with text only."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
            "status": "submitted",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="What files are in this directory?",
        )

        self.mock_http_client.post.assert_called_once()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session/abc123/prompt_async")
        self.assertEqual(kwargs["json"]["text"], "What files are in this directory?")
        self.assertIn("message_id", kwargs["json"])

    def test_submit_prompt_with_agent(self):
        """Test submit_prompt() with agent parameter."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            agent="gpt-4",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs["json"]["agent"], "gpt-4")

    def test_submit_prompt_with_system_prompt(self):
        """Test submit_prompt() with system_prompt."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            system_prompt="You are a helpful assistant",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs["json"]["system_prompt"], "You are a helpful assistant")

    def test_submit_prompt_with_tools_config(self):
        """Test submit_prompt() with tools configuration."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        tools = {"bash": True, "git": True}

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            tools=tools,
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs["json"]["tools"], tools)

    def test_submit_prompt_autogenerates_message_id(self):
        """Test submit_prompt() auto-generates message_id if not provided."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "generated_id",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("message_id", kwargs["json"])
        # Should be UUID-like
        message_id = kwargs["json"]["message_id"]
        self.assertIsNotNone(message_id)
        self.assertGreater(len(message_id), 0)

    def test_submit_prompt_with_custom_message_id(self):
        """Test submit_prompt() with custom message_id."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "custom_id",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            message_id="custom_id",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs["json"]["message_id"], "custom_id")

    def test_submit_prompt_abort_false_no_abort_call(self):
        """Test submit_prompt() with abort=False doesn't call abort."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            abort=False,
        )

        # Should only have one POST call (for submit, not abort)
        post_calls = [c for c in self.mock_http_client.method_calls if "post" in str(c)]
        self.assertEqual(len(post_calls), 1)

    def test_submit_prompt_abort_true(self):
        """Test submit_prompt() with abort=True calls abort first."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            abort=True,
        )

        # Should have two POST calls: abort + submit
        post_calls = [
            c for c in self.mock_http_client.method_calls if "post" in str(c).lower()
        ]
        # Check that both calls were made (order: abort first, then submit)
        self.assertGreaterEqual(len(post_calls), 2)

    def test_abort_session_succeeds(self):
        """Test abort_session() succeeds."""
        self.mock_http_client.post.return_value.json.return_value = {}

        self.submitter.abort_session(session_id="abc123")

        self.mock_http_client.post.assert_called()
        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(args[0], "/session/abc123/abort")

    def test_abort_session_not_found(self):
        """Test abort_session() with 404 error."""
        self.mock_http_client.post.return_value.raise_for_status.side_effect = (
            Exception("404 Not Found")
        )

        with self.assertRaises(Exception):
            self.submitter.abort_session(session_id="nonexistent")

    def test_submit_prompt_with_directory_context(self):
        """Test submit_prompt() includes directory context."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            directory="/custom/dir",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertEqual(kwargs.get("directory"), "/custom/dir")

    def test_submit_prompt_with_provider_and_model_id(self):
        """Test submit_prompt() with provider_id and model_id."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            provider_id="nvidia",
            model_id="nim",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("model", kwargs["json"])
        self.assertEqual(kwargs["json"]["model"]["providerID"], "nvidia")
        self.assertEqual(kwargs["json"]["model"]["modelID"], "nim")

    def test_submit_prompt_with_provider_id_only(self):
        """Test submit_prompt() with provider_id only."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            provider_id="openai",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("model", kwargs["json"])
        self.assertEqual(kwargs["json"]["model"]["providerID"], "openai")
        self.assertNotIn("modelID", kwargs["json"]["model"])

    def test_submit_prompt_with_model_id_only(self):
        """Test submit_prompt() with model_id only."""
        self.mock_http_client.post.return_value.json.return_value = {
            "message_id": "msg123",
        }

        result = self.submitter.submit_prompt(
            session_id="abc123",
            text="Hello",
            model_id="gpt-4",
        )

        args, kwargs = self.mock_http_client.post.call_args
        self.assertIn("model", kwargs["json"])
        self.assertEqual(kwargs["json"]["model"]["modelID"], "gpt-4")
        self.assertNotIn("providerID", kwargs["json"]["model"])
