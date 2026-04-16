"""Prompt submission for sending prompts to OpenCode sessions.

This module provides the PromptSubmitter class which handles submitting
prompts/messages to sessions and managing session abortion.

Typical usage:
    >>> from opencode_server_client.prompt.sync_submitter import PromptSubmitter
    >>> submitter = PromptSubmitter(http_client)
    >>> result = submitter.submit_prompt(
    ...     session_id="abc123",
    ...     text="What is the file structure?",
    ...     abort=True  # abort current processing first
    ... )
    >>> print(f"Message ID: {result['message_id']}")
"""

import logging
import uuid
from typing import Any, Dict, Optional

from opencode_server_client.http_client.sync_client import SyncHttpClient

logger = logging.getLogger(__name__)


class PromptSubmitter:
    """Submit prompts and manage session abortion via HTTP API.

    This class handles:
    - Submitting prompts/messages to sessions
    - Optional abort-before-submit logic
    - Session abortion

    Attributes:
        http_client: SyncHttpClient instance for HTTP requests
    """

    def __init__(self, http_client: SyncHttpClient):
        """Initialize the PromptSubmitter.

        Args:
            http_client: SyncHttpClient instance for making requests
        """
        self.http_client = http_client

    def submit_prompt(
        self,
        session_id: str,
        text: str,
        message_id: Optional[str] = None,
        agent: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None,
        abort: bool = False,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a prompt to a session.

        Args:
            session_id: ID of the session
            text: Prompt text to send
            message_id: Optional message ID (auto-generated if not provided)
            agent: Optional agent name/config
            system_prompt: Optional system prompt override
            tools: Optional tools configuration
            abort: If True, abort session before submitting (default: False)
            directory: Optional directory context

        Returns:
            Response dict with message_id and other metadata

        Raises:
            PromptSubmissionError: If submission fails
            SessionNotFoundError: If session not found
        """
        # Generate message_id if not provided
        if not message_id:
            message_id = str(uuid.uuid4())

        # Abort first if requested
        if abort:
            try:
                self.abort_session(session_id, directory=directory)
            except Exception as e:
                logger.warning(f"Failed to abort session during submit: {e}")
                # Continue with submission anyway

        # Build the payload
        payload = {
            "text": text,
            "message_id": message_id,
        }

        if agent:
            payload["agent"] = agent
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if tools:
            payload["tools"] = tools

        try:
            response = self.http_client.post(
                f"/session/{session_id}/prompt_async",
                json=payload,
                directory=directory,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to submit prompt to session {session_id}: {e}")
            raise

    def abort_session(
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
            response = self.http_client.post(
                f"/session/{session_id}/abort",
                directory=directory,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to abort session {session_id}: {e}")
            raise
