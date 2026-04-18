"""Async prompt submission for sending prompts to OpenCode sessions.

This module provides the AsyncPromptSubmitter class which handles submitting
prompts/messages to sessions asynchronously and managing session abortion.

Typical usage:
    >>> from opencode_server_client.http_client.async_client import AsyncHttpClient
    >>> from opencode_server_client.prompt.async_submitter import AsyncPromptSubmitter
    >>> config = ServerConfig(base_url="http://localhost:8000")
    >>> async with AsyncHttpClient(config) as http_client:
    ...     submitter = AsyncPromptSubmitter(http_client)
    ...     result = await submitter.submit_prompt(
    ...         session_id="abc123",
    ...         text="What is the file structure?",
    ...         provider_id="nvidia",
    ...         model_id="nim",
    ...         abort=True  # abort current processing first
    ...     )
    ...     print(f"Message ID: {result['message_id']}")
"""

import logging
from typing import Any, Dict, Optional

from opencode_server_client.http_client.async_client import AsyncHttpClient
from opencode_server_client.identifiers import generate_message_id, generate_part_id

logger = logging.getLogger(__name__)


class AsyncPromptSubmitter:
    """Submit prompts and manage session abortion via async HTTP API.

    This class handles:
    - Submitting prompts/messages to sessions asynchronously
    - Optional abort-before-submit logic
    - Session abortion

    Attributes:
        http_client: AsyncHttpClient instance for HTTP requests
    """

    def __init__(self, http_client: AsyncHttpClient):
        """Initialize the AsyncPromptSubmitter.

        Args:
            http_client: AsyncHttpClient instance for making requests
        """
        self.http_client = http_client

    async def submit_prompt(
        self,
        session_id: str,
        text: str,
        message_id: Optional[str] = None,
        agent: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
        abort: bool = False,
        directory: Optional[str] = None,
    ) -> str:
        """Submit a prompt to a session asynchronously.

        Args:
            session_id: ID of the session
            text: Prompt text to send
            message_id: Optional message ID (auto-generated if not provided)
            agent: Optional agent name/config
            system_prompt: Optional system prompt override
            tools: Optional tools configuration
            provider_id: Optional provider ID (e.g., "anthropic", "openai")
            model_id: Optional model ID (e.g., "opus-4.6", "gpt-5.4")
            abort: If True, abort session before submitting (default: False)
            directory: Optional directory context

        Returns:
            (str) The ID of the submitted message.

        Raises:
            PromptSubmissionError: If submission fails
            SessionNotFoundError: If session not found
        """
        if not message_id:
            message_id = generate_message_id()

        if abort:
            try:
                await self.abort_session(session_id, directory=directory)
            except Exception as e:
                logger.warning(f"Failed to abort session during submit: {e}")

        payload = {
            "parts": [{"type": "text", "text": text, "id": generate_part_id()}],
            "messageID": message_id,
        }

        if agent:
            payload["agent"] = agent
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if tools:
            payload["tools"] = tools
        if provider_id or model_id:
            payload["model"] = {}
            if provider_id:
                payload["model"]["providerID"] = provider_id
            if model_id:
                payload["model"]["modelID"] = model_id

        try:
            response = await self.http_client.post(
                f"/session/{session_id}/prompt_async",
                json=payload,
                directory=directory,
            )
            response.raise_for_status()
            return message_id
        except Exception as e:
            logger.error(f"Failed to submit prompt to session {session_id}: {e}")
            raise

    async def abort_session(
        self,
        session_id: str,
        directory: Optional[str] = None,
    ) -> None:
        """Abort current processing in a session.

        Args:
            session_id: ID of the session to abort
            directory: Optional directory context

        Raises:
            SessionNotFoundError: If session not found (404)
            PromptSubmissionError: If abortion fails
        """
        try:
            response = await self.http_client.post(
                f"/session/{session_id}/abort",
                directory=directory,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to abort session {session_id}: {e}")
            raise
