"""Tests for asynchronous HTTP client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.exceptions import RetryExhaustedError
from opencode_server_client.http_client.async_client import (
    AsyncHttpClient,
    calculate_backoff_delay,
)


class TestAsyncHttpClientInit:
    """Test AsyncHttpClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default retry config."""
        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        assert client.server_config == config
        assert client.retry_config.max_retries == 3
        assert client.retry_config.initial_delay == 1.0

    def test_init_with_custom_retry_config(self):
        """Test initialization with custom retry config."""
        server_config = ServerConfig(base_url="http://localhost:8000")
        retry_config = RetryConfig(max_retries=5, initial_delay=2.0)
        client = AsyncHttpClient(server_config, retry_config)

        assert client.retry_config.max_retries == 5
        assert client.retry_config.initial_delay == 2.0

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager support."""
        config = ServerConfig(base_url="http://localhost:8000")
        async with AsyncHttpClient(config) as client:
            assert client is not None


class TestAsyncHttpClientRetry:
    """Test retry logic in AsyncHttpClient."""

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_successful_request_no_retry(self, mock_client_class):
        """Test successful async request without retries."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.get("/api/sessions")

        assert response.status_code == 200
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    @patch(
        "opencode_server_client.http_client.async_client.asyncio.sleep",
        new_callable=AsyncMock,
    )
    async def test_502_retry_then_success(self, mock_sleep, mock_client_class):
        """Test 502 error triggers async retry, then succeeds."""
        mock_response_502 = Mock(spec=httpx.Response)
        mock_response_502.status_code = 502

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(
            side_effect=[mock_response_502, mock_response_200]
        )
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.get("/api/sessions")

        assert response.status_code == 200
        assert mock_client.request.call_count == 2
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    @patch(
        "opencode_server_client.http_client.async_client.asyncio.sleep",
        new_callable=AsyncMock,
    )
    async def test_503_retry_then_success(self, mock_sleep, mock_client_class):
        """Test 503 error triggers async retry, then succeeds."""
        mock_response_503 = Mock(spec=httpx.Response)
        mock_response_503.status_code = 503

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(
            side_effect=[mock_response_503, mock_response_200]
        )
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.post("/api/sessions", json={"test": "data"})

        assert response.status_code == 200
        assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_transport_error_retry(self, mock_client_class):
        """Test that async transport errors trigger retries."""
        transport_error = httpx.TransportError("Connection refused")
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=[transport_error, mock_response])
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.get("/api/sessions")

        assert response.status_code == 200
        assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_transport_error_exhausted(self, mock_client_class):
        """Test that exhausted async transport errors raise RetryExhaustedError."""
        transport_error = httpx.TransportError("Connection refused")

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=transport_error)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        retry_config = RetryConfig(max_retries=2)
        client = AsyncHttpClient(config, retry_config)

        with pytest.raises(RetryExhaustedError):
            await client.get("/api/sessions")

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_directory_header_included(self, mock_client_class):
        """Test that X-Opencode-Directory header is included in async requests."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        await client.get("/api/sessions", directory="/path/to/dir")

        call_kwargs = mock_client.request.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["X-Opencode-Directory"] == "/path/to/dir"


class TestAsyncHttpClientMethods:
    """Test individual async HTTP methods."""

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_get_method(self, mock_client_class):
        """Test async GET method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.get("/api/sessions")

        assert response.status_code == 200
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_post_method(self, mock_client_class):
        """Test async POST method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.post("/api/sessions", json={"name": "test"})

        assert response.status_code == 201
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_delete_method(self, mock_client_class):
        """Test async DELETE method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.delete("/api/sessions/123")

        assert response.status_code == 204
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    @patch("opencode_server_client.http_client.async_client.httpx.AsyncClient")
    async def test_request_method_generic(self, mock_client_class):
        """Test generic async request method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = AsyncHttpClient(config)

        response = await client.request(
            "PATCH", "/api/sessions/123", json={"status": "active"}
        )

        assert response.status_code == 200
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "PATCH"
