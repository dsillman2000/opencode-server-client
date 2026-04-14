"""Session management for Opencode."""

import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

import httpx

from .types import SessionInfo, WorkspaceInfo


class TempOpencodeSession:
    """Context manager for creating and managing Opencode sessions.

    Supports both simple sessions and sessions with worktrees/workspaces.
    """

    _worktree_creation_lock = threading.Lock()
    _last_worktree_created_at = 0.0

    def __init__(
        self,
        client: httpx.Client,
        use_worktree: bool = False,
        directory: Optional[Path] = None,
        create_workspace: bool = False,
        workspace_creation_spacing_seconds: float = 0.5,
        logger: Optional[Callable[[str], None]] = None,
    ):
        """Initialize session manager.

        Args:
            client: httpx.Client configured for Opencode API
            use_worktree: Whether to create a worktree for this session
            directory: Base directory to use/create
            create_workspace: Whether to create a workspace in the worktree
            workspace_creation_spacing_seconds: Minimum delay between worktree
                creation requests across concurrent sessions
            logger: Optional logging function
        """
        self.client = client
        self.use_worktree = use_worktree
        self.directory = directory or Path(__file__).parent
        self.project_directory = self.directory
        self.create_workspace = create_workspace
        self.workspace_creation_spacing_seconds = workspace_creation_spacing_seconds
        self.logger = logger or (lambda _: None)
        self.session: Optional[dict[str, Any]] = None
        self.workspace: Optional[WorkspaceInfo] = None

    def _create_worktree(self) -> WorkspaceInfo:
        """Create a worktree with throttling across concurrent sessions."""
        session_cls = type(self)
        with session_cls._worktree_creation_lock:
            if self.workspace_creation_spacing_seconds > 0:
                now = time.monotonic()
                elapsed = now - session_cls._last_worktree_created_at
                remaining = self.workspace_creation_spacing_seconds - elapsed
                if remaining > 0:
                    self.logger(f"Waiting {remaining:.3f}s before creating next workspace")
                    time.sleep(remaining)
            worktree_id = uuid.uuid4().hex
            resp = self.client.post(
                "/experimental/worktree",
                params={
                    "directory": str(self.directory),
                    "worktreeCreateInput": {"name": f"wrk_{worktree_id}"},
                },
            )
            resp.raise_for_status()
            workspace = WorkspaceInfo(**resp.json())
            session_cls._last_worktree_created_at = time.monotonic()
            return workspace

    def __enter__(self) -> SessionInfo:
        """Create and enter session context."""
        project_directory = str(self.project_directory)

        if self.use_worktree:
            self.workspace = self._create_worktree()
            self.directory = Path(self.workspace["directory"])
            self.logger(f"Workspace {self.workspace['name']} created at {self.directory}")
            time.sleep(3)  # Give workspace time to be ready

            resp = self.client.get("/project/current", params={"directory": str(self.directory)})
            resp.raise_for_status()
            proj = resp.json()
            self.logger(f"Current project: {proj}")
            self.workspace["projectID"] = proj["id"]

        self.client.headers.update({"X-Opencode-Directory": str(self.directory)})
        resp = self.client.post("/session", json={"directory": str(self.directory)})
        resp.raise_for_status()
        self.session = resp.json()
        self.logger(f"Session {self.session['id']} created at {self.directory}")

        return SessionInfo(
            id=self.session["id"],
            directory=str(self.directory),
            project_directory=project_directory,
            branch=self.workspace["branch"] if self.workspace else None,
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit session context (cleanup handled by caller if needed)."""
        return None

    def cleanup(self) -> None:
        """Explicitly clean up the session."""
        if self.session:
            session_id = self.session["id"]
            try:
                resp = self.client.delete(f"/session/{session_id}")
                resp.raise_for_status()
                self.logger(f"Session {session_id} deleted successfully")
            except Exception as e:
                self.logger(f"Failed to delete session {session_id}: {e}")

    def cleanup_worktree(self) -> None:
        """Explicitly clean up the worktree if one was created."""
        if self.workspace:
            worktree_directory = self.workspace["directory"]
            project_directory = str(self.project_directory)
            try:
                resp = self.client.request(
                    "DELETE",
                    "/experimental/worktree",
                    params={"directory": project_directory},
                    json={"directory": worktree_directory},
                )
                resp.raise_for_status()
                self.logger(f"Workspace {self.workspace['name']} deleted successfully")
            except Exception as e:
                self.logger(f"Failed to delete workspace {worktree_directory}: {e}")
