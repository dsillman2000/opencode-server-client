"""HTTP client management for Opencode API."""

import time
from typing import Any, Optional

import httpx

from .types import WorkspaceInfo


class RetryingOpencodeClient(httpx.Client):
    """httpx client with basic retry handling for intermittent gateway errors."""

    def __init__(
        self,
        *args: Any,
        gateway_retry_attempts: int = 0,
        gateway_retry_delay_seconds: float = 0.5,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.gateway_retry_attempts = gateway_retry_attempts
        self.gateway_retry_delay_seconds = gateway_retry_delay_seconds

    def request(self, method: str, url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
        """Retry 502 gateway failures and transient transport errors."""
        attempt = 0

        while True:
            try:
                response = super().request(method, url, *args, **kwargs)
            except httpx.TransportError:
                if attempt >= self.gateway_retry_attempts:
                    raise
                attempt += 1
                time.sleep(self.gateway_retry_delay_seconds)
                continue

            if response.status_code != 502 or attempt >= self.gateway_retry_attempts:
                return response

            response.close()
            attempt += 1
            time.sleep(self.gateway_retry_delay_seconds)


def create_http_client(
    base_url: str,
    basic_auth: str,
    timeout: float = 60.0,
    gateway_retry_attempts: int = 0,
    gateway_retry_delay_seconds: float = 0.5,
) -> httpx.Client:
    """Create and configure an httpx.Client for Opencode API.

    Args:
        base_url: Base URL of the Opencode server
        basic_auth: Base64-encoded basic auth credentials
        timeout: Request timeout in seconds
        gateway_retry_attempts: Number of automatic retries for 502 gateway
            failures after the initial request
        gateway_retry_delay_seconds: Delay between gateway retry attempts

    Returns:
        Configured httpx.Client
    """
    headers: dict[str, str] = {}
    if basic_auth:
        headers["Authorization"] = f"Basic {basic_auth}"

    return RetryingOpencodeClient(
        base_url=base_url,
        headers=headers,
        timeout=timeout,
        gateway_retry_attempts=gateway_retry_attempts,
        gateway_retry_delay_seconds=gateway_retry_delay_seconds,
    )


def nvidia_provider(client: httpx.Client) -> Optional[dict[str, Any]]:
    """Fetch NVIDIA provider information from Opencode API.

    Args:
        client: httpx.Client configured for Opencode API

    Returns:
        Provider info dict or None if not available
    """
    resp = client.get("/config/providers")
    resp.raise_for_status()
    providers = resp.json()["providers"]
    return next((p for p in providers if p["id"] == "nvidia"), None)
