"""Tests for synchronous HTTP client."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from opencode_server_client.config import RetryConfig, ServerConfig
from opencode_server_client.exceptions import RetryExhaustedError
from opencode_server_client.http_client.sync_client import (
    SyncHttpClient,
    calculate_backoff_delay,
)


class TestCalculateBackoffDelay:
    """Test exponential backoff delay calculation."""

    def test_first_retry_delay(self):
        """Test delay for first retry attempt."""
        delay = calculate_backoff_delay(0, 1.0, 30.0, 2.0)
        assert delay == 1.0

    def test_exponential_growth(self):
        """Test that delay grows exponentially."""
        delay0 = calculate_backoff_delay(0, 1.0, 30.0, 2.0)
        delay1 = calculate_backoff_delay(1, 1.0, 30.0, 2.0)
        delay2 = calculate_backoff_delay(2, 1.0, 30.0, 2.0)

        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        delay = calculate_backoff_delay(10, 1.0, 30.0, 2.0)
        assert delay == 30.0

    def test_custom_initial_delay(self):
        """Test with custom initial delay."""
        delay = calculate_backoff_delay(0, 5.0, 60.0, 2.0)
        assert delay == 5.0


class TestSyncHttpClientInit:
    """Test SyncHttpClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default retry config."""
        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        assert client.server_config == config
        assert client.retry_config.max_retries == 3
        assert client.retry_config.initial_delay == 1.0

    def test_init_with_custom_retry_config(self):
        """Test initialization with custom retry config."""
        server_config = ServerConfig(base_url="http://localhost:8000")
        retry_config = RetryConfig(max_retries=5, initial_delay=2.0)
        client = SyncHttpClient(server_config, retry_config)

        assert client.retry_config.max_retries == 5
        assert client.retry_config.initial_delay == 2.0

    def test_context_manager(self):
        """Test context manager support."""
        config = ServerConfig(base_url="http://localhost:8000")
        with SyncHttpClient(config) as client:
            assert client is not None


class TestSyncHttpClientRetry:
    """Test retry logic in SyncHttpClient."""

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_successful_request_no_retry(self, mock_client_class):
        """Test successful request without retries."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.get("/api/sessions")

        assert response.status_code == 200
        mock_client.request.assert_called_once()

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    @patch("opencode_server_client.http_client.sync_client.time.sleep")
    def test_502_retry_then_success(self, mock_sleep, mock_client_class):
        """Test 502 error triggers retry, then succeeds."""
        mock_response_502 = Mock(spec=httpx.Response)
        mock_response_502.status_code = 502

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        mock_client = MagicMock()
        mock_client.request.side_effect = [mock_response_502, mock_response_200]
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.get("/api/sessions")

        assert response.status_code == 200
        assert mock_client.request.call_count == 2
        mock_sleep.assert_called_once()

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    @patch("opencode_server_client.http_client.sync_client.time.sleep")
    def test_503_retry_then_success(self, mock_sleep, mock_client_class):
        """Test 503 error triggers retry, then succeeds."""
        mock_response_503 = Mock(spec=httpx.Response)
        mock_response_503.status_code = 503

        mock_response_200 = Mock(spec=httpx.Response)
        mock_response_200.status_code = 200

        mock_client = MagicMock()
        mock_client.request.side_effect = [mock_response_503, mock_response_200]
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.post("/api/sessions", json={"test": "data"})

        assert response.status_code == 200
        assert mock_client.request.call_count == 2

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_404_not_retried(self, mock_client_class):
        """Test that 404 errors are NOT retried."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        mock_client.request.assert_called_once()

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    @patch("opencode_server_client.http_client.sync_client.time.sleep")
    def test_transport_error_retry(self, mock_sleep, mock_client_class):
        """Test that transport errors trigger retries."""
        transport_error = httpx.TransportError("Connection refused")
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request.side_effect = [transport_error, mock_response]
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.get("/api/sessions")

        assert response.status_code == 200
        assert mock_client.request.call_count == 2
        mock_sleep.assert_called_once()

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    @patch("opencode_server_client.http_client.sync_client.time.sleep")
    def test_retry_exhausted(self, mock_sleep, mock_client_class):
        """Test that retry exhaustion raises error."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 503

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        retry_config = RetryConfig(max_retries=2)
        client = SyncHttpClient(config, retry_config)

        response = client.get("/api/sessions")

        # After max_retries, we return the last response (503)
        assert response.status_code == 503
        assert mock_client.request.call_count == 3  # initial + 2 retries

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_transport_error_exhausted(self, mock_client_class):
        """Test that exhausted transport errors raise RetryExhaustedError."""
        transport_error = httpx.TransportError("Connection refused")

        mock_client = MagicMock()
        mock_client.request.side_effect = transport_error
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        retry_config = RetryConfig(max_retries=2)
        client = SyncHttpClient(config, retry_config)

        with pytest.raises(RetryExhaustedError):
            client.get("/api/sessions")

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_directory_header_included(self, mock_client_class):
        """Test that X-Opencode-Directory header is included."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        client.get("/api/sessions", directory="/path/to/dir")

        call_kwargs = mock_client.request.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["X-Opencode-Directory"] == "/path/to/dir"


class TestSyncHttpClientMethods:
    """Test individual HTTP methods."""

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_get_method(self, mock_client_class):
        """Test GET method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.get("/api/sessions")

        assert response.status_code == 200
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_post_method(self, mock_client_class):
        """Test POST method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.post("/api/sessions", json={"name": "test"})

        assert response.status_code == 201
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_delete_method(self, mock_client_class):
        """Test DELETE method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.delete("/api/sessions/123")

        assert response.status_code == 204
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "DELETE"

    @patch("opencode_server_client.http_client.sync_client.httpx.Client")
    def test_request_method_generic(self, mock_client_class):
        """Test generic request method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200

        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ServerConfig(base_url="http://localhost:8000")
        client = SyncHttpClient(config)

        response = client.request(
            "PATCH", "/api/sessions/123", json={"status": "active"}
        )

        assert response.status_code == 200
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "PATCH"
