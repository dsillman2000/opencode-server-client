"""MLflow Opencode - High-level API for running parallel experiments on Opencode servers."""

# Samplers submodule
from . import samplers
from .client import create_http_client, nvidia_provider
from .config import (
    ExperimentConfig,
    OpencodeServerConfig,
    always_retry_policy,
    no_retry_policy,
    timeout_retry_policy,
    timeout_with_retry_policy,
)
from .experiment import OpencodeExperiment
from .io import append_log, write_json_artifact
from .session import TempOpencodeSession
from .streaming import StreamingPrompt
from .types import (
    ChatTurnTimeout,
    ExperimentResult,
    RetryDecision,
    SessionContext,
    SessionSetupConfig,
    ValidationError,
)

__all__ = [
    # Main classes
    "OpencodeExperiment",
    "ExperimentConfig",
    "OpencodeServerConfig",
    "SessionContext",
    "ExperimentResult",
    "SessionSetupConfig",
    "RetryDecision",
    # Low-level APIs
    "TempOpencodeSession",
    "StreamingPrompt",
    "create_http_client",
    "nvidia_provider",
    # Retry policies
    "no_retry_policy",
    "timeout_retry_policy",
    "timeout_with_retry_policy",
    "always_retry_policy",
    # I/O utilities
    "append_log",
    "write_json_artifact",
    # Exceptions
    "ChatTurnTimeout",
    "ValidationError",
    # Submodules
    "samplers",
]
