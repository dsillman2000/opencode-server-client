"""Async Session Manager for CRUD operations on OpenCode sessions.

This module provides the AsyncSessionManager class which handles creating,
listing, getting, updating, and deleting OpenCode sessions via async HTTP API.

Typical usage:
    >>> from opencode_server_client.http_client.async_client import AsyncHttpClient
    >>> from opencode_server_client.session.async_manager import AsyncSessionManager
    >>> config = ServerConfig(base_url="http://localhost:8000")
    >>> async with AsyncHttpClient(config) as http_client:
    ...     manager = AsyncSessionManager(http_client, default_directory="/path/to/project")
    ...     session = await manager.create(title="New Session")
    ...     print(f"Created session: {session['session_id']}")
"""

import logging
from typing import Any, Dict, List, Optional

from opencode_server_client.http_client.async_client import AsyncHttpClient

logger = logging.getLogger(__name__)


class AsyncSessionManager:
    """Manage OpenCode sessions via async HTTP API.

    This class provides async methods for creating, listing, getting, updating,
    and deleting sessions. It wraps the async HTTP client and handles directory
    context (passed via X-Opencode-Directory header).

    Attributes:
        http_client: AsyncHttpClient instance for HTTP requests
        default_directory: Default directory context for operations
    """

    def __init__(
        self,
        http_client: AsyncHttpClient,
        default_directory: Optional[str] = None,
    ):
        """Initialize the AsyncSessionManager.

        Args:
            http_client: AsyncHttpClient instance for making requests
            default_directory: Optional default directory for all operations
        """
        self.http_client = http_client
        self.default_directory = default_directory

    async def create(
        self,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new OpenCode session.

        Args:
            title: Optional title for the session
            parent_id: Optional parent session ID for nested sessions
            directory: Optional directory context (overrides default)

        Returns:
            Session metadata dict with session_id, created_at, etc.

        Raises:
            SessionCreationError: If session creation fails
        """
        dir_context = directory or self.default_directory

        payload = {}
        if title:
            payload["title"] = title
        if parent_id:
            payload["parent_id"] = parent_id

        try:
            response = await self.http_client.post(
                "/session",
                json=payload if payload else None,
                directory=dir_context,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def list(
        self,
        directory: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all sessions in a directory.

        Args:
            directory: Optional directory context (overrides default)

        Returns:
            List of session metadata dicts

        Raises:
            SessionError: If listing fails
        """
        dir_context = directory or self.default_directory

        try:
            response = await self.http_client.get(
                "/session",
                directory=dir_context,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "sessions" in data:
                return data["sessions"]
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise

    async def get(
        self,
        session_id: str,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get metadata for a specific session.

        Args:
            session_id: ID of the session to retrieve
            directory: Optional directory context (overrides default)

        Returns:
            Session metadata dict

        Raises:
            SessionNotFoundError: If session not found (404)
            SessionError: If retrieval fails
        """
        dir_context = directory or self.default_directory

        try:
            response = await self.http_client.get(
                f"/session/{session_id}",
                directory=dir_context,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise

    async def update(
        self,
        session_id: str,
        title: Optional[str] = None,
        parent_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing session.

        This is useful for renaming a session title or changing its parent.

        Args:
            session_id: ID of the session to update
            title: Optional new title for the session
            parent_id: Optional new parent session ID
            directory: Optional directory context (overrides default)

        Returns:
            Updated session metadata dict

        Raises:
            ValueError: If no update fields were provided
            SessionError: If the update fails
        """
        dir_context = directory or self.default_directory

        payload = {}
        if title is not None:
            payload["title"] = title
        if parent_id is not None:
            payload["parent_id"] = parent_id

        if not payload:
            raise ValueError("At least one field must be provided to update a session")

        try:
            response = await self.http_client.request(
                "PATCH",
                f"/session/{session_id}",
                json=payload,
                directory=dir_context,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise

    async def delete(
        self,
        session_id: str,
        directory: Optional[str] = None,
    ) -> None:
        """Delete a session.

        Args:
            session_id: ID of the session to delete
            directory: Optional directory context (overrides default)

        Raises:
            SessionNotFoundError: If session not found (404)
            SessionError: If deletion fails
        """
        dir_context = directory or self.default_directory

        try:
            response = await self.http_client.delete(
                f"/session/{session_id}",
                directory=dir_context,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
