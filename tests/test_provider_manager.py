"""Unit tests for provider manager and types."""

import unittest
from unittest.mock import Mock

from opencode_server_client.config import ServerConfig  # ruff: noqa F401
from opencode_server_client.provider.sync_manager import ProviderManager
from opencode_server_client.provider.types import ModelCost  # ruff: noqa F401
from opencode_server_client.provider.types import (
    InputCapabilities,
    Model,
    ModelCapabilities,
    OutputCapabilities,
    Provider,
    ProviderList,
)


class TestModelCapabilities(unittest.TestCase):
    """Test ModelCapabilities dataclass."""

    def test_has_text_io_true(self):
        """Test has_text_io returns True when both input and output text are supported."""
        caps = ModelCapabilities(
            input=InputCapabilities(text=True),
            output=OutputCapabilities(text=True),
        )
        self.assertTrue(caps.has_text_io())

    def test_has_text_io_false_missing_input(self):
        """Test has_text_io returns False when input is missing."""
        caps = ModelCapabilities(output=OutputCapabilities(text=True))
        self.assertFalse(caps.has_text_io())

    def test_has_text_io_false_missing_output(self):
        """Test has_text_io returns False when output is missing."""
        caps = ModelCapabilities(input=InputCapabilities(text=True))
        self.assertFalse(caps.has_text_io())

    def test_has_toolcall_true(self):
        """Test has_toolcall returns True."""
        caps = ModelCapabilities(toolcall=True)
        self.assertTrue(caps.has_toolcall())

    def test_has_toolcall_false(self):
        """Test has_toolcall returns False."""
        caps = ModelCapabilities(toolcall=False)
        self.assertFalse(caps.has_toolcall())

    def test_has_reasoning_true(self):
        """Test has_reasoning returns True."""
        caps = ModelCapabilities(reasoning=True)
        self.assertTrue(caps.has_reasoning())


class TestModel(unittest.TestCase):
    """Test Model dataclass."""

    def test_from_dict_basic(self):
        """Test creating Model from dict."""
        data = {
            "id": "gpt-4",
            "capabilities": {
                "input": {"text": True},
                "output": {"text": True},
                "toolcall": True,
            },
            "cost": {"input": 0.03, "output": 0.06},
        }

        model = Model.from_dict(data)

        self.assertEqual(model.id, "gpt-4")
        self.assertTrue(model.capabilities.has_text_io())
        self.assertTrue(model.capabilities.has_toolcall())
        self.assertEqual(model.cost.input, 0.03)
        self.assertEqual(model.cost.output, 0.06)

    def test_from_dict_without_cost(self):
        """Test creating Model from dict without cost."""
        data = {
            "id": "model-1",
            "capabilities": {
                "input": {"text": True},
                "output": {"text": True},
            },
        }

        model = Model.from_dict(data)

        self.assertEqual(model.id, "model-1")
        self.assertIsNone(model.cost)

    def test_from_dict_with_reasoning(self):
        """Test creating Model with reasoning capability."""
        data = {
            "id": "reasoning-model",
            "capabilities": {
                "input": {"text": True},
                "output": {"text": True},
                "reasoning": True,
            },
        }

        model = Model.from_dict(data)

        self.assertTrue(model.capabilities.has_reasoning())


class TestProvider(unittest.TestCase):
    """Test Provider dataclass."""

    def test_from_dict(self):
        """Test creating Provider from dict."""
        data = {
            "models": {
                "gpt-4": {
                    "capabilities": {
                        "input": {"text": True},
                        "output": {"text": True},
                        "toolcall": True,
                    },
                },
                "gpt-3.5": {
                    "capabilities": {
                        "input": {"text": True},
                        "output": {"text": True},
                    },
                },
            }
        }

        provider = Provider.from_dict("openai", data)

        self.assertEqual(provider.id, "openai")
        self.assertEqual(len(provider.models), 2)
        self.assertIn("gpt-4", provider.models)
        self.assertIn("gpt-3.5", provider.models)

    def test_get_model(self):
        """Test getting a specific model."""
        data = {
            "models": {
                "gpt-4": {
                    "capabilities": {
                        "input": {"text": True},
                        "output": {"text": True},
                    },
                }
            }
        }

        provider = Provider.from_dict("openai", data)
        model = provider.get_model("gpt-4")

        self.assertIsNotNone(model)
        self.assertEqual(model.id, "gpt-4")

    def test_get_model_not_found(self):
        """Test getting a non-existent model."""
        data = {"models": {}}
        provider = Provider.from_dict("openai", data)
        model = provider.get_model("gpt-999")

        self.assertIsNone(model)

    def test_list_text_capable_models(self):
        """Test listing text-capable models."""
        data = {
            "models": {
                "text-model": {
                    "capabilities": {
                        "input": {"text": True},
                        "output": {"text": True},
                    },
                },
                "no-text-model": {
                    "capabilities": {
                        "input": {"text": False},
                        "output": {"text": False},
                    },
                },
            }
        }

        provider = Provider.from_dict("test", data)
        models = provider.list_text_capable_models()

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].id, "text-model")

    def test_list_models_with_capabilities(self):
        """Test filtering models by capabilities."""
        data = {
            "models": {
                "full-model": {
                    "capabilities": {
                        "input": {"text": True},
                        "output": {"text": True},
                        "toolcall": True,
                    },
                },
                "text-only": {
                    "capabilities": {
                        "input": {"text": True},
                        "output": {"text": True},
                        "toolcall": False,
                    },
                },
            }
        }

        provider = Provider.from_dict("test", data)

        # Filter by text capability
        text_models = provider.list_models_with_capabilities(text_capable=True)
        self.assertEqual(len(text_models), 2)

        # Filter by toolcall capability
        toolcall_models = provider.list_models_with_capabilities(toolcall=True)
        self.assertEqual(len(toolcall_models), 1)
        self.assertEqual(toolcall_models[0].id, "full-model")


class TestProviderList(unittest.TestCase):
    """Test ProviderList dataclass."""

    def test_from_dict(self):
        """Test creating ProviderList from dict."""
        data = {
            "all": {
                "openai": {
                    "models": {
                        "gpt-4": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
                "anthropic": {
                    "models": {
                        "claude-3": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
            },
            "connected": ["openai"],
        }

        provider_list = ProviderList.from_dict(data)

        self.assertEqual(len(provider_list.all), 2)
        self.assertEqual(provider_list.connected, ["openai"])

    def test_get_provider(self):
        """Test getting a specific provider."""
        data = {
            "all": {
                "openai": {
                    "models": {
                        "gpt-4": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                }
            },
            "connected": ["openai"],
        }

        provider_list = ProviderList.from_dict(data)
        provider = provider_list.get_provider("openai")

        self.assertIsNotNone(provider)
        self.assertEqual(provider.id, "openai")

    def test_is_connected(self):
        """Test checking if provider is connected."""
        data = {
            "all": {
                "openai": {"models": {}},
                "anthropic": {"models": {}},
            },
            "connected": ["openai"],
        }

        provider_list = ProviderList.from_dict(data)

        self.assertTrue(provider_list.is_connected("openai"))
        self.assertFalse(provider_list.is_connected("anthropic"))

    def test_list_connected_providers(self):
        """Test listing connected providers."""
        data = {
            "all": {
                "openai": {
                    "models": {
                        "gpt-4": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
                "anthropic": {
                    "models": {
                        "claude-3": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
            },
            "connected": ["openai"],
        }

        provider_list = ProviderList.from_dict(data)
        connected = provider_list.list_connected_providers()

        self.assertEqual(len(connected), 1)
        self.assertEqual(connected[0].id, "openai")


class TestProviderManager(unittest.TestCase):
    """Test ProviderManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_http_client = Mock()
        self.manager = ProviderManager(self.mock_http_client)

    def test_list_providers(self):
        """Test listing all providers."""
        api_response = {
            "all": {
                "deepseek": {
                    "models": {
                        "deepseek-chat": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                }
            },
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        providers = self.manager.list_providers()

        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0].id, "deepseek")

    def test_list_providers_connected_only(self):
        """Test listing only connected providers."""
        api_response = {
            "all": {
                "deepseek": {"models": {}},
                "openai": {"models": {}},
            },
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        providers = self.manager.list_providers(connected_only=True)

        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0].id, "deepseek")

    def test_get_provider(self):
        """Test getting a specific provider."""
        api_response = {
            "all": {
                "deepseek": {
                    "models": {
                        "deepseek-chat": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                }
            },
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        provider = self.manager.get_provider("deepseek")

        self.assertIsNotNone(provider)
        self.assertEqual(provider.id, "deepseek")

    def test_get_model(self):
        """Test getting a specific model."""
        api_response = {
            "all": {
                "deepseek": {
                    "models": {
                        "deepseek-chat": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                }
            },
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        model = self.manager.get_model("deepseek", "deepseek-chat")

        self.assertIsNotNone(model)
        self.assertEqual(model.id, "deepseek-chat")

    def test_find_model(self):
        """Test finding a model across providers."""
        api_response = {
            "all": {
                "openai": {
                    "models": {
                        "gpt-4": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
                "deepseek": {
                    "models": {
                        "deepseek-chat": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
            },
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        provider_id, model = self.manager.find_model("deepseek-chat")

        self.assertEqual(provider_id, "deepseek")
        self.assertEqual(model.id, "deepseek-chat")

    def test_find_model_not_found(self):
        """Test finding a model that doesn't exist."""
        api_response = {
            "all": {"deepseek": {"models": {}}},
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        provider_id, model = self.manager.find_model("nonexistent")

        self.assertIsNone(provider_id)
        self.assertIsNone(model)

    def test_list_text_capable_models(self):
        """Test listing text-capable models."""
        api_response = {
            "all": {
                "deepseek": {
                    "models": {
                        "deepseek-chat": {
                            "capabilities": {
                                "input": {"text": True},
                                "output": {"text": True},
                            }
                        }
                    }
                },
                "vision-provider": {
                    "models": {
                        "vision-model": {
                            "capabilities": {
                                "input": {"text": False},
                                "output": {"text": False},
                            }
                        }
                    }
                },
            },
            "connected": ["deepseek", "vision-provider"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        models = self.manager.list_text_capable_models()

        self.assertIn("deepseek", models)
        self.assertEqual(len(models["deepseek"]), 1)
        self.assertNotIn("vision-provider", models)

    def test_is_provider_connected(self):
        """Test checking if provider is connected."""
        api_response = {
            "all": {
                "deepseek": {"models": {}},
                "openai": {"models": {}},
            },
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        self.assertTrue(self.manager.is_provider_connected("deepseek"))
        self.assertFalse(self.manager.is_provider_connected("openai"))

    def test_cache_reuse(self):
        """Test that cache is reused on multiple calls."""
        api_response = {
            "all": {"deepseek": {"models": {}}},
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        # First call
        self.manager.list_providers()
        # Second call
        self.manager.list_providers()

        # HTTP call should only be made once
        self.mock_http_client.get.assert_called_once()

    def test_refresh_cache(self):
        """Test that refresh clears the cache."""
        api_response = {
            "all": {"deepseek": {"models": {}}},
            "connected": ["deepseek"],
        }

        self.mock_http_client.get.return_value.json.return_value = api_response

        # First call
        self.manager.list_providers()
        # Refresh cache
        self.manager.refresh_cache()
        # Second call
        self.manager.list_providers()

        # HTTP call should be made twice
        self.assertEqual(self.mock_http_client.get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
