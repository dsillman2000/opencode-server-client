"""Core type definitions for mlflow_opencode module."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, TypedDict


class WorkspaceInfo(TypedDict):
    """Information about a created Opencode workspace."""

    branch: str
    projectID: str
    directory: str
    name: str


class SessionInfo(TypedDict):
    """Session information returned by Opencode API."""

    id: str
    directory: str
    project_directory: str
    branch: Optional[str]


@dataclass
class RetryDecision:
    """Decision returned by a retry policy."""

    should_retry: bool
    custom_prompt: Optional[str] = None
    reason: str = ""


@dataclass
class SessionContext:
    """Context passed to user task functions.

    Provides both high-level convenience methods and low-level access
    to the Opencode session.
    """

    session_id: str
    model: str
    prompt: str
    workspace_directory: Optional[Path]
    attempt: int
    chat_turn_timeout_seconds: int
    logger: Callable[[str], None]
    client: Any  # httpx.Client (imported to avoid circular deps)
    last_chat_turn_output: Optional[dict[str, Any]] = None

    def run_prompt(self) -> str:
        """Execute the current prompt and return the assistant response.

        Uses StreamingPrompt under the hood to stream response updates.
        """
        # Import here to avoid circular imports
        import time

        from .streaming import StreamingPrompt

        start_time = time.monotonic()
        with StreamingPrompt(self.client, self.session_id, self.model, self.prompt) as streaming_prompt:
            while not streaming_prompt.finished():
                if time.monotonic() - start_time > self.chat_turn_timeout_seconds:
                    self.logger(
                        f"Chat turn timed out after {self.chat_turn_timeout_seconds}s; aborting session {self.session_id}"
                    )
                    streaming_prompt.abort()
                    raise ChatTurnTimeout(f"Chat turn exceeded timeout of {self.chat_turn_timeout_seconds} seconds")
                streaming_prompt.refresh_messages()
                time.sleep(0.2)
            self.last_chat_turn_output = streaming_prompt.turn_output()
            return streaming_prompt.assistant_text()


@dataclass
class ExperimentResult:
    """Result from running a single session in an experiment.

    Attributes:
        session_id: Unique session identifier
        model: Model ID used in this session
        prompt_hash: SHA256 hash of the prompt
        workspace_directory: Path to workspace if created with worktree
        output: User-defined output from task function
        status: Final status (OK or ERROR)
        error: Error message if status is ERROR
        execution_time_seconds: Total execution time
    """

    session_id: str
    model: str
    prompt_hash: str
    workspace_directory: Optional[Path]
    output: Any
    status: str  # "OK" or "ERROR"
    error: Optional[str] = None
    execution_time_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dict for MLflow outputs."""
        return {
            "session_id": self.session_id,
            "model": self.model,
            "prompt_hash": self.prompt_hash,
            "workspace_directory": str(self.workspace_directory) if self.workspace_directory else None,
            "output": self.output,
            "status": self.status,
            "error": self.error,
            "execution_time_seconds": self.execution_time_seconds,
        }


@dataclass
class SessionSetupConfig:
    """Configuration for setting up a session.

    Attributes:
        use_worktree: Whether to create and use a worktree for this session
        directory: Base directory for the session (used if use_worktree=False)
        create_workspace: Whether to create a new workspace in the worktree
    """

    use_worktree: bool = False
    directory: Optional[Path] = None
    create_workspace: bool = False


# Type aliases for common callable patterns
SessionSetupFactory = Callable[[int], SessionSetupConfig]
PromptSampler = Callable[[int], str]
ModelSampler = Callable[[int], str]
RetryPolicy = Callable[[int, Exception, SessionContext], RetryDecision]


# Custom exceptions
class ChatTurnTimeout(Exception):
    """Raised when a chat turn (agent reasoning step) times out."""

    pass


class ValidationError(Exception):
    """Raised when task validation fails."""

    pass
    pass
