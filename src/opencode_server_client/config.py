"""Configuration dataclasses for HTTP client."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for OpenCode server connection.

    Attributes:
        base_url: The base URL of the OpenCode server (e.g., "http://localhost:8000")
        basic_auth: Optional tuple of (username, password) for HTTP Basic Auth
        timeout: Request timeout in seconds (default: 30)
    """

    base_url: str
    basic_auth: Optional[Tuple[str, str]] = None
    timeout: float = 30.0


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for exponential backoff retry logic.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 30.0)
        exponential_base: Base multiplier for exponential backoff (default: 2.0)

    Raises:
        ValueError: If exponential_base <= 1.0
    """

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

    def __post_init__(self):
        """Validate retry configuration."""
        if self.exponential_base <= 1.0:
            raise ValueError(
                f"exponential_base must be > 1.0, got {self.exponential_base}"
            )
