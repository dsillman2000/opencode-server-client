"""Tests for AsyncProviderManager - async provider management."""

import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock

from opencode_server_client.provider.async_manager import AsyncProviderManager


class TestAsyncProviderManager(TestCase):
    """Test AsyncProviderManager async operations."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.mock_http_client.get = AsyncMock()
        self.manager = AsyncProviderManager(self.mock_http_client)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()

    def _setup_mock_response(self, data):
        """Set up mock HTTP response."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = data
        self.mock_http_client.get.return_value = mock_response

    def test_list_providers(self):
        """Test list_providers() fetches and returns providers."""
        self._setup_mock_response(
            {
                "all": {
                    "openai": {
                        "models": {
                            "gpt-4": {
                                "id": "gpt-4",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": True},
                                },
                            }
                        }
                    }
                },
                "connected": ["openai"],
            }
        )

        result = self.loop.run_until_complete(self.manager.list_providers())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "openai")
        self.mock_http_client.get.assert_called_once_with("/provider")

    def test_get_provider(self):
        """Test get_provider() returns specific provider."""
        self._setup_mock_response(
            {
                "all": {
                    "openai": {
                        "models": {
                            "gpt-4": {
                                "id": "gpt-4",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": True},
                                },
                            }
                        }
                    }
                },
                "connected": [],
            }
        )

        result = self.loop.run_until_complete(self.manager.get_provider("openai"))

        self.assertIsNotNone(result)
        self.assertEqual(result.id, "openai")

    def test_get_provider_not_found(self):
        """Test get_provider() returns None for unknown provider."""
        self._setup_mock_response({"all": {"openai": {"models": {}}}, "connected": []})

        result = self.loop.run_until_complete(self.manager.get_provider("unknown"))

        self.assertIsNone(result)

    def test_get_model(self):
        """Test get_model() returns specific model from provider."""
        self._setup_mock_response(
            {
                "all": {
                    "openai": {
                        "models": {
                            "gpt-4": {
                                "id": "gpt-4",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": True},
                                },
                            }
                        }
                    }
                },
                "connected": [],
            }
        )

        result = self.loop.run_until_complete(self.manager.get_model("openai", "gpt-4"))

        self.assertIsNotNone(result)
        self.assertEqual(result.id, "gpt-4")

    def test_get_model_not_found(self):
        """Test get_model() returns None for unknown model."""
        self._setup_mock_response({"all": {"openai": {"models": {}}}, "connected": []})

        result = self.loop.run_until_complete(
            self.manager.get_model("openai", "unknown")
        )

        self.assertIsNone(result)

    def test_find_model(self):
        """Test find_model() finds model across providers."""
        self._setup_mock_response(
            {
                "all": {
                    "openai": {
                        "models": {
                            "gpt-4": {
                                "id": "gpt-4",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": True},
                                },
                            }
                        }
                    },
                    "anthropic": {
                        "models": {
                            "opus": {
                                "id": "opus",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": True},
                                },
                            }
                        }
                    },
                },
                "connected": [],
            }
        )

        provider_id, model = self.loop.run_until_complete(
            self.manager.find_model("opus")
        )

        self.assertEqual(provider_id, "anthropic")
        self.assertIsNotNone(model)
        self.assertEqual(model.id, "opus")

    def test_find_model_not_found(self):
        """Test find_model() returns (None, None) when not found."""
        self._setup_mock_response({"all": {"openai": {"models": {}}}, "connected": []})

        result = self.loop.run_until_complete(self.manager.find_model("unknown"))

        self.assertEqual(result, (None, None))

    def test_list_providers_connected_only(self):
        """Test list_providers() with connected_only filter."""
        self._setup_mock_response(
            {
                "all": {
                    "openai": {"models": {}},
                    "anthropic": {"models": {}},
                },
                "connected": ["openai"],
            }
        )

        result = self.loop.run_until_complete(
            self.manager.list_providers(connected_only=True)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "openai")

    def test_list_text_capable_models(self):
        """Test list_text_capable_models() returns text-capable models."""
        self._setup_mock_response(
            {
                "all": {
                    "openai": {
                        "models": {
                            "gpt-4": {
                                "id": "gpt-4",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": True},
                                },
                            },
                            "gpt-3.5": {
                                "id": "gpt-3.5",
                                "capabilities": {
                                    "input": {"text": True},
                                    "output": {"text": False},
                                },
                            },
                        }
                    }
                },
                "connected": ["openai"],
            }
        )

        result = self.loop.run_until_complete(
            self.manager.list_text_capable_models(connected_only=True)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(len(result["openai"]), 1)
        self.assertEqual(result["openai"][0].id, "gpt-4")

    def test_is_provider_connected(self):
        """Test is_provider_connected() checks connection status."""
        self._setup_mock_response(
            {"all": {"openai": {"models": {}}}, "connected": ["openai"]}
        )

        result = self.loop.run_until_complete(
            self.manager.is_provider_connected("openai")
        )

        self.assertTrue(result)

    def test_is_provider_not_connected(self):
        """Test is_provider_connected() returns False for disconnected."""
        self._setup_mock_response({"all": {"openai": {"models": {}}}, "connected": []})

        result = self.loop.run_until_complete(
            self.manager.is_provider_connected("openai")
        )

        self.assertFalse(result)

    def test_cache_reuse(self):
        """Test that provider data is cached and reused."""
        self._setup_mock_response({"all": {"openai": {"models": {}}}, "connected": []})

        self.loop.run_until_complete(self.manager.list_providers())
        self.loop.run_until_complete(self.manager.get_provider("openai"))

        self.mock_http_client.get.assert_called_once()

    def test_refresh_cache(self):
        """Test refresh_cache() clears cache and refetches."""
        self._setup_mock_response({"all": {"openai": {"models": {}}}, "connected": []})

        self.loop.run_until_complete(self.manager.list_providers())
        self.loop.run_until_complete(self.manager.refresh_cache())
        self.loop.run_until_complete(self.manager.list_providers())

        self.assertEqual(self.mock_http_client.get.call_count, 2)
