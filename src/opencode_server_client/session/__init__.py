"""Session management for creating and managing OpenCode sessions.

This module provides:
- SessionManager: CRUD operations for sessions (sync)
- (Future) AsyncSessionManager: CRUD operations for sessions (async)

Typical usage:
    >>> from opencode_server_client.session import SessionManager
    >>> manager = SessionManager(http_client, default_directory="/path")
    >>> session = manager.create(title="New Session")
"""

from opencode_server_client.session.sync_manager import SessionManager

__all__ = ["SessionManager"]
