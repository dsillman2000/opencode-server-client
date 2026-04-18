"""Main OpenCode server client - asynchronous API.

This module provides the AsyncOpencodeServerClient class which aggregates
session management, prompt submission, and event subscription into a single
high-level async interface.

Typical usage:
    >>> from opencode_server_client.client_async import AsyncOpencodeServerClient
    >>> from opencode_server_client.config import ServerConfig
    >>>
    >>> config = ServerConfig(base_url="http://localhost:8000")
    >>> async with AsyncOpencodeServerClient(config, default_directory="/path/to/project") as client:
    ...     # Simple workflow: create session, submit prompt, wait for response
    ...     session = await client.create_session()
    ...     messages = await client.submit_prompt_and_wait(
    ...         session_id=session["session_id"],
    ...         text="What files are in this project?",
    ...         timeout=30.0
    ...     )
    ...     for message in messages:
    ...         print(message)
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.events.async_subscriber import AsyncEventSubscriber
from opencode_server_client.events.types import MessageUpdatedEvent, SessionIdleEvent
from opencode_server_client.http_client.async_client import AsyncHttpClient
from opencode_server_client.prompt.async_submitter import AsyncPromptSubmitter
from opencode_server_client.provider.sync_manager import ProviderManager
from opencode_server_client.session.async_manager import AsyncSessionManager

logger = logging.getLogger(__name__)


class AsyncOpencodeServerClient:
    """Main asynchronous client for OpenCode server operations.

    This client aggregates:
    - ProviderManager: Query available providers and their models
    - AsyncSessionManager: Create, list, get, delete sessions
    - AsyncPromptSubmitter: Submit prompts with optional abort
    - AsyncEventSubscriber: Subscribe to real-time events via SSE

    It also provides convenience methods for common workflows like
    "submit and wait for response".

    Attributes:
        providers: ProviderManager instance
        sessions: AsyncSessionManager instance
        prompts: AsyncPromptSubmitter instance
        events: AsyncEventSubscriber instance
    """

    def __init__(
        self,
        server_config: ServerConfig,
        retry_config: Optional[RetryConfig] = None,
        default_directory: Optional[str] = None,
    ):
        """Initialize the async OpenCode server client.

        Args:
            server_config: Server connection configuration
            retry_config: Retry behavior configuration (optional)
            default_directory: Default directory context for operations
        """
        self.server_config = server_config
        self.retry_config = retry_config or RetryConfig()
        self.default_directory = default_directory

        self._http_client = AsyncHttpClient(server_config, retry_config)

        self.providers = ProviderManager(self._http_client)
        self.sessions = AsyncSessionManager(self._http_client, default_directory)
        self.prompts = AsyncPromptSubmitter(self._http_client)
        self.events = AsyncEventSubscriber(self._http_client)

    async def __aenter__(self) -> "AsyncOpencodeServerClient":
        """Async context manager entry."""
        await self._http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - cleanup resources."""
        await self.close()
        return False

    async def close(self) -> None:
        """Close the client and cleanup resources.

        This stops the event subscriber asyncio task and closes
        the HTTP client.
        """
        logger.debug("Closing AsyncOpencodeServerClient")
        await self.events.close()
        await self._http_client.__aexit__(None, None, None)

    async def create_session(
        self,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new session.

        Args:
            title: Optional session title
            parent_id: Optional parent session ID
            directory: Optional directory context

        Returns:
            Session metadata dict
        """
        return await self.sessions.create(
            title=title, parent_id=parent_id, directory=directory
        )

    async def list_all_sessions(
        self, directory: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all sessions in a directory.

        Args:
            directory: Optional directory context

        Returns:
            List of session metadata dicts
        """
        return await self.sessions.list(directory=directory)

    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing session.

        Args:
            session_id: ID of session to update
            title: Optional new session title
            parent_id: Optional new parent session ID
            directory: Optional directory context

        Returns:
            Updated session metadata dict
        """
        return await self.sessions.update(
            session_id,
            title=title,
            parent_id=parent_id,
            directory=directory,
        )

    async def patch_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Alias for update_session()."""
        return await self.update_session(
            session_id,
            title=title,
            parent_id=parent_id,
            directory=directory,
        )

    async def delete_session(
        self, session_id: str, directory: Optional[str] = None
    ) -> None:
        """Delete a session.

        Args:
            session_id: ID of session to delete
            directory: Optional directory context
        """
        await self.sessions.delete(session_id, directory=directory)

    async def submit_prompt_and_wait(
        self,
        session_id: str,
        text: str,
        timeout: float = 30.0,
        abort: bool = False,
        poll_interval: float = 0.2,
        on_message: Optional[Callable[[MessageUpdatedEvent], Any]] = None,
        directory: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Submit a prompt and wait for the session to become idle.

        This is a convenience method that combines:
        1. Subscribing to events for the session
        2. Submitting the prompt
        3. Waiting for session.idle event
        4. Collecting all message.updated events

        Args:
            session_id: ID of session to submit to
            text: Prompt text
            timeout: Maximum time to wait for idle (seconds)
            abort: If True, abort session before submitting
            poll_interval: Polling interval for checking session status
            on_message: Optional callback for each message event
            directory: Optional directory context

        Returns:
            List of messages collected during wait (from message.updated events)

        Raises:
            TimeoutError: If timeout exceeded before session became idle
        """
        messages: List[Dict[str, Any]] = []
        idle_event = asyncio.Event()

        async def handle_message(event: MessageUpdatedEvent):
            messages.append(
                {
                    "message_id": event.message_id,
                    "content": event.content,
                    "timestamp": event.timestamp.isoformat(),
                }
            )
            if on_message:
                await on_message(event)

        async def handle_idle(event: SessionIdleEvent):
            idle_event.set()

        await self.events.subscribe(
            on_event=lambda e: (
                handle_message(e) if isinstance(e, MessageUpdatedEvent) else None
            ),
            on_idle=handle_idle,
            session_id_filter=session_id,
        )

        try:
            await self.prompts.submit_prompt(
                session_id=session_id,
                text=text,
                abort=abort,
                directory=directory,
            )

            start_time = asyncio.get_event_loop().time()
            while not idle_event.is_set():
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError(
                        f"Session {session_id} did not become idle within {timeout}s"
                    )
                await asyncio.sleep(poll_interval)

            return messages

        finally:
            pass
