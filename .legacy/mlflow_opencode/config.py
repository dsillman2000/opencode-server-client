"""Configuration and retry policy definitions."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .types import (
    ChatTurnTimeout,
    ModelSampler,
    PromptSampler,
    RetryDecision,
    RetryPolicy,
    SessionContext,
    SessionSetupFactory,
)


@dataclass(frozen=True)
class OpencodeServerConfig:
    """Configuration for Opencode server connection."""

    base_url: str
    basic_auth: str


@dataclass(frozen=True)
class ExperimentConfig:
    """Complete configuration for an experiment run.

    Attributes:
        server: Opencode server connection details
        mlflow_tracking_uri: MLflow tracking server URI
        mlflow_experiment_name: Name of MLflow experiment
        parallel_session_count: Total number of sessions to run
        max_active_session_count: Maximum concurrent sessions
        chat_turn_timeout_seconds: Timeout for a single agent reasoning turn
        output_dir: Directory for output artifacts
        max_retries_per_session: Maximum retry attempts per session
        gateway_retry_attempts: Number of automatic retries for intermittent
            502 gateway failures after the initial request
        gateway_retry_delay_seconds: Delay between gateway retry attempts
        workspace_creation_spacing_seconds: Minimum delay between worktree
            creation requests across concurrent sessions
        clean_up_sessions: Whether to delete sessions after completion
        clean_up_worktrees: Whether to delete worktrees after completion
        clean_up_session: Deprecated alias for clean_up_sessions
        clean_up_worktree: Deprecated alias for clean_up_worktrees
        cleanup_sessions: Deprecated alias for clean_up_sessions
        prompt_sampler: Function that returns prompt for a given session index
        model_sampler: Function that returns model for a given session index
        retry_policy: Optional custom retry policy
        session_setup_factory: Optional custom session setup factory
        workspace_files_to_capture: Workspace-relative or absolute file paths to
            capture on the session span via the Opencode file content API
    """

    server: OpencodeServerConfig
    mlflow_tracking_uri: str
    mlflow_experiment_name: str
    parallel_session_count: int
    max_active_session_count: int
    chat_turn_timeout_seconds: int
    output_dir: Path
    prompt_sampler: PromptSampler
    model_sampler: ModelSampler
    max_retries_per_session: int = 1
    gateway_retry_attempts: int = 2
    gateway_retry_delay_seconds: float = 0.5
    workspace_creation_spacing_seconds: float = 0.5
    clean_up_sessions: bool = True
    clean_up_worktrees: bool = True
    clean_up_session: Optional[bool] = None
    clean_up_worktree: Optional[bool] = None
    cleanup_sessions: Optional[bool] = None
    retry_policy: Optional[RetryPolicy] = None
    session_setup_factory: Optional[SessionSetupFactory] = None
    workspace_files_to_capture: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize deprecated cleanup configuration."""
        if self.clean_up_session is not None:
            object.__setattr__(self, "clean_up_sessions", self.clean_up_session)

        if self.clean_up_worktree is not None:
            object.__setattr__(self, "clean_up_worktrees", self.clean_up_worktree)

        if self.cleanup_sessions is not None:
            object.__setattr__(self, "clean_up_sessions", self.cleanup_sessions)


# Built-in retry policies


DEFAULT_TIMEOUT_RETRY_ATTEMPTS = 2
DEFAULT_TIMEOUT_RETRY_PROMPT = "Your previous response timed out. Please try again, being concise."


def no_retry_policy(attempt: int, error: Exception, ctx: SessionContext) -> RetryDecision:
    """Never retry - fail on first error."""
    return RetryDecision(should_retry=False, reason=f"Error: {error}")


def _timeout_retry_decision(
    attempt: int,
    error: Exception,
    max_timeout_attempts: int,
    custom_prompt: str,
) -> RetryDecision:
    """Build a retry decision for timeout-driven retries."""
    if isinstance(error, ChatTurnTimeout) and attempt < max_timeout_attempts:
        return RetryDecision(
            should_retry=True,
            custom_prompt=custom_prompt,
            reason="ChatTurnTimeout detected, retrying with guidance...",
        )
    return RetryDecision(should_retry=False, reason=str(error))


def timeout_retry_policy(
    max_timeout_attempts: int = DEFAULT_TIMEOUT_RETRY_ATTEMPTS,
    custom_prompt: str = DEFAULT_TIMEOUT_RETRY_PROMPT,
) -> RetryPolicy:
    """Create a retry policy that retries chat turn timeouts up to a limit.

    Args:
        max_timeout_attempts: Total number of timeout attempts allowed, including
            the initial attempt.
        custom_prompt: Prompt override to use on timeout retries.
    """
    if max_timeout_attempts < 1:
        raise ValueError("max_timeout_attempts must be at least 1")

    def policy(attempt: int, error: Exception, ctx: SessionContext) -> RetryDecision:
        return _timeout_retry_decision(
            attempt=attempt,
            error=error,
            max_timeout_attempts=max_timeout_attempts,
            custom_prompt=custom_prompt,
        )

    return policy


def timeout_with_retry_policy(attempt: int, error: Exception, ctx: SessionContext) -> RetryDecision:
    """Default timeout retry policy.

    This preserves the original callable RetryPolicy shape while the configurable
    factory is exposed via timeout_retry_policy(...).
    """
    return _timeout_retry_decision(
        attempt=attempt,
        error=error,
        max_timeout_attempts=DEFAULT_TIMEOUT_RETRY_ATTEMPTS,
        custom_prompt=DEFAULT_TIMEOUT_RETRY_PROMPT,
    )


def always_retry_policy(attempt: int, error: Exception, ctx: SessionContext) -> RetryDecision:
    """Retry up to max_retries on any error."""
    # Note: max_retries limit is enforced by experiment runner
    return RetryDecision(should_retry=True, reason=f"Attempt {attempt} failed: {error}, retrying...")
