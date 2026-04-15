"""Asynchronous HTTP client with retry logic for OpenCode server communication."""

import asyncio
import logging
from typing import Any, Optional

import httpx

from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)


def calculate_backoff_delay(
    attempt: int, initial_delay: float, max_delay: float, exponential_base: float
) -> float:
    """Calculate exponential backoff delay for a retry attempt.

    Args:
        attempt: Zero-indexed attempt number (0 = first retry)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base multiplier for exponential backoff

    Returns:
        Delay in seconds, capped at max_delay
    """
    delay = initial_delay * (exponential_base**attempt)
    return min(delay, max_delay)


class AsyncHttpClient:
    """Asynchronous HTTP client with exponential backoff retry logic.

    This client automatically retries transient failures (502, 503, transport errors)
    with exponential backoff using asyncio. It supports async context manager protocol
    for automatic resource cleanup.

    Example:
        >>> config = ServerConfig(base_url="http://localhost:8000")
        >>> retry = RetryConfig(max_retries=3)
        >>> async with AsyncHttpClient(config, retry) as client:
        ...     response = await client.get("/api/sessions")
    """

    def __init__(
        self, server_config: ServerConfig, retry_config: Optional[RetryConfig] = None
    ):
        """Initialize the asynchronous HTTP client.

        Args:
            server_config: Server connection configuration
            retry_config: Retry behavior configuration (uses defaults if None)
        """
        self.server_config = server_config
        self.retry_config = retry_config or RetryConfig()
        self._client = httpx.AsyncClient(
            base_url=server_config.base_url,
            auth=server_config.basic_auth,
            timeout=server_config.timeout,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close the client."""
        await self._client.aclose()
        return False

    def _should_retry(self, status_code: int, is_transport_error: bool) -> bool:
        """Determine if an error should be retried.

        Args:
            status_code: HTTP status code (0 if transport error)
            is_transport_error: Whether this is a transport-level error

        Returns:
            True if the error should be retried, False otherwise
        """
        if is_transport_error:
            return True
        return status_code in (502, 503)

    async def _request_with_retry(
        self, method: str, url: str, directory: Optional[str] = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform an async HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            url: URL path (relative to base_url)
            directory: Optional directory context (sent via X-Opencode-Directory header)
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            HTTP response object

        Raises:
            RetryExhaustedError: If all retry attempts are exhausted
        """
        headers = kwargs.get("headers", {})
        if isinstance(headers, dict):
            headers = dict(headers)  # Make a copy
        else:
            headers = dict(headers)

        if directory:
            headers["X-Opencode-Directory"] = directory

        kwargs["headers"] = headers

        last_exception = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self._client.request(method, url, **kwargs)

                # Check if we should retry based on status code
                if attempt < self.retry_config.max_retries and self._should_retry(
                    response.status_code, False
                ):
                    delay = calculate_backoff_delay(
                        attempt,
                        self.retry_config.initial_delay,
                        self.retry_config.max_delay,
                        self.retry_config.exponential_base,
                    )
                    logger.debug(
                        f"Retrying {method} {url} after {response.status_code}, "
                        f"attempt {attempt + 1}/{self.retry_config.max_retries}, "
                        f"delay: {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Success or non-retryable error
                return response

            except httpx.TransportError as e:
                last_exception = e
                if attempt < self.retry_config.max_retries:
                    delay = calculate_backoff_delay(
                        attempt,
                        self.retry_config.initial_delay,
                        self.retry_config.max_delay,
                        self.retry_config.exponential_base,
                    )
                    logger.debug(
                        f"Transport error on {method} {url}, "
                        f"attempt {attempt + 1}/{self.retry_config.max_retries}, "
                        f"delay: {delay}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise RetryExhaustedError(
                        f"Transport error after {self.retry_config.max_retries} retries: {e}"
                    ) from e

        # Should not reach here, but raise if we do
        if last_exception:
            raise last_exception
        raise RetryExhaustedError(
            f"Request failed after {self.retry_config.max_retries} retries"
        )

    async def get(
        self, url: str, directory: Optional[str] = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform an async GET request with retry logic.

        Args:
            url: URL path (relative to base_url)
            directory: Optional directory context
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object
        """
        return await self._request_with_retry("GET", url, directory=directory, **kwargs)

    async def post(
        self, url: str, directory: Optional[str] = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform an async POST request with retry logic.

        Args:
            url: URL path (relative to base_url)
            directory: Optional directory context
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object
        """
        return await self._request_with_retry(
            "POST", url, directory=directory, **kwargs
        )

    async def delete(
        self, url: str, directory: Optional[str] = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform an async DELETE request with retry logic.

        Args:
            url: URL path (relative to base_url)
            directory: Optional directory context
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object
        """
        return await self._request_with_retry(
            "DELETE", url, directory=directory, **kwargs
        )

    async def request(
        self, method: str, url: str, directory: Optional[str] = None, **kwargs: Any
    ) -> httpx.Response:
        """Perform an async generic HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            url: URL path (relative to base_url)
            directory: Optional directory context
            **kwargs: Additional arguments to pass to httpx

        Returns:
            HTTP response object
        """
        return await self._request_with_retry(
            method, url, directory=directory, **kwargs
        )
