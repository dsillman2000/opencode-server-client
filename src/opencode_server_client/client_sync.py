"""Main OpenCode server client - synchronous API.

This module provides the primary OpencodeServerClient class which aggregates
session management, prompt submission, and event subscription into a single
high-level interface.

Typical usage:
    >>> from opencode_server_client.client_sync import OpencodeServerClient
    >>> from opencode_server_client.config import ServerConfig
    >>>
    >>> config = ServerConfig(base_url="http://localhost:8000")
    >>> client = OpencodeServerClient(config, default_directory="/path/to/project")
    >>>
    >>> # Simple workflow: create session, submit prompt, wait for response
    >>> session = client.create_session()
    >>> messages = client.submit_prompt_and_wait(
    ...     session_id=session["session_id"],
    ...     text="What files are in this project?",
    ...     timeout=30.0
    ... )
    >>>
    >>> with client:
    ...     # Context manager ensures cleanup
    ...     for message in messages:
    ...         print(message)
"""

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.events.sync_subscriber import EventSubscriber
from opencode_server_client.events.types import AnyEvent, SessionIdleEvent
from opencode_server_client.http_client.sync_client import SyncHttpClient
from opencode_server_client.prompt.sync_submitter import PromptSubmitter
from opencode_server_client.provider.sync_manager import ProviderManager
from opencode_server_client.session.sync_manager import SessionManager

logger = logging.getLogger(__name__)


class OpencodeServerClient:
    """Main synchronous client for OpenCode server operations.

    This client aggregates four layers:
    - ProviderManager: Query available providers and their models
    - SessionManager: Create, list, get, delete sessions
    - PromptSubmitter: Submit prompts with optional abort
    - EventSubscriber: Subscribe to real-time events via SSE

    It also provides convenience methods for common workflows like
    "submit and wait for response".

    Attributes:
        providers: ProviderManager instance
        sessions: SessionManager instance
        prompts: PromptSubmitter instance
        events: EventSubscriber instance
    """

    def __init__(
        self,
        server_config: ServerConfig,
        retry_config: Optional[RetryConfig] = None,
        default_directory: Optional[str] = None,
    ):
        """Initialize the OpenCode server client.

        Args:
            server_config: Server connection configuration
            retry_config: Retry behavior configuration (optional)
            default_directory: Default directory context for operations
        """
        self.server_config = server_config
        self.retry_config = retry_config or RetryConfig()
        self.default_directory = default_directory

        # Create HTTP client
        self._http_client = SyncHttpClient(server_config, retry_config)

        # Create managers
        self.providers = ProviderManager(self._http_client)
        self.sessions = SessionManager(self._http_client, default_directory)
        self.prompts = PromptSubmitter(self._http_client)
        self.events = EventSubscriber(self._http_client)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
        return False

    def close(self) -> None:
        """Close the client and cleanup resources.

        This stops the event subscriber background thread and closes
        the HTTP client.
        """
        logger.debug("Closing OpencodeServerClient")
        self.events.close()
        self._http_client.__exit__(None, None, None)

    # Convenience methods

    def create_session(
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
        return self.sessions.create(
            title=title, parent_id=parent_id, directory=directory
        )

    def list_all_sessions(
        self, directory: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all sessions in a directory.

        Args:
            directory: Optional directory context

        Returns:
            List of session metadata dicts
        """
        return self.sessions.list(directory=directory)

    def update_session(
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
        return self.sessions.update(
            session_id,
            title=title,
            parent_id=parent_id,
            directory=directory,
        )

    def patch_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Alias for update_session()."""
        return self.update_session(
            session_id,
            title=title,
            parent_id=parent_id,
            directory=directory,
        )

    def delete_session(self, session_id: str, directory: Optional[str] = None) -> None:
        """Delete a session.

        Args:
            session_id: ID of session to delete
            directory: Optional directory context
        """
        self.sessions.delete(session_id, directory=directory)

    def submit_prompt_and_wait(
        self,
        session_id: str,
        text: str,
        timeout: float = 30.0,
        abort: bool = False,
        on_event: Optional[Callable[[AnyEvent], None]] = None,
        directory: Optional[str] = None,
        model_id: Optional[str] = None,
        provider_id: Optional[str] = None,
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
            on_event: Optional callback for each event (MessageUpdatedEvent, etc.)
            directory: Optional directory context
            model_id: Optional model ID (e.g., "big-pickle", "opus-4.6")
            provider_id: Optional provider ID (e.g., "opencode", "anthropic")

        Returns:
            List of messages collected during wait (from message.updated events)

        Raises:
            TimeoutError: If timeout exceeded before session became idle
        """
        messages: List[Dict[str, Any]] = []
        idle_event = threading.Event()

        def handle_idle(_: SessionIdleEvent):
            idle_event.set()

        # Subscribe to events
        self.events.subscribe(
            on_event=on_event,
            on_idle=handle_idle,
            session_id_filter=session_id,
        )

        # Submit the prompt
        try:
            self.prompts.submit_prompt(
                session_id=session_id,
                text=text,
                directory=directory,
                model_id=model_id,
                provider_id=provider_id,
            )

            # Wait for idle event or timeout
            if not idle_event.wait(timeout=timeout):
                if abort:
                    self.prompts.abort_session(
                        session_id=session_id, directory=directory
                    )
                raise TimeoutError(
                    f"Session {session_id} did not become idle within {timeout}s"
                )

            return messages

        finally:
            # Note: We could unsubscribe here, but leaving subscriptions
            # allows for multiple prompts without resubscribing
            pass
