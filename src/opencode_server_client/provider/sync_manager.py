"""Synchronous provider manager for OpenCode server."""

import logging
from typing import Optional

from opencode_server_client.http_client.sync_client import SyncHttpClient
from opencode_server_client.provider.types import Provider, ProviderList

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manage providers and models from the OpenCode server.

    Provides user-friendly APIs for querying available providers, their models,
    and filtering by capabilities.

    Example:
        >>> manager = ProviderManager(http_client)
        >>> providers = manager.list_providers()
        >>> deepseek = manager.get_provider("deepseek")
        >>> model = deepseek.get_model("deepseek-chat")
        >>> if model.capabilities.has_text_io():
        ...     print(f"Model {model.id} supports text I/O")
    """

    def __init__(self, http_client: SyncHttpClient):
        """Initialize the ProviderManager.

        Args:
            http_client: SyncHttpClient instance for making requests
        """
        self.http_client = http_client
        self._cache: Optional[ProviderList] = None

    def _fetch_providers(self, use_cache: bool = True) -> ProviderList:
        """Fetch providers from the server.

        Args:
            use_cache: Whether to use cached results (default: True)

        Returns:
            ProviderList with all providers and their models
        """
        if use_cache and self._cache is not None:
            return self._cache

        response = self.http_client.get("/provider")
        response.raise_for_status()
        data = response.json()

        providers = ProviderList.from_dict(data)
        self._cache = providers
        return providers

    def list_providers(self, connected_only: bool = False) -> list[Provider]:
        """Get all providers.

        Args:
            connected_only: If True, only return connected providers (default: False)

        Returns:
            List of Provider objects
        """
        providers = self._fetch_providers()

        if connected_only:
            return providers.list_connected_providers()

        return list(providers.all.values())

    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get a specific provider by ID.

        Args:
            provider_id: The provider ID (e.g., "deepseek", "nvidia")

        Returns:
            Provider object, or None if not found
        """
        providers = self._fetch_providers()
        return providers.get_provider(provider_id)

    def get_model(self, provider_id: str, model_id: str) -> Optional[Provider]:
        """Get a specific model from a provider.

        Args:
            provider_id: The provider ID
            model_id: The model ID

        Returns:
            Model object, or None if not found
        """
        provider = self.get_provider(provider_id)
        if provider is None:
            return None
        return provider.get_model(model_id)

    def find_model(self, model_id: str) -> tuple[Optional[str], Optional[Provider]]:
        """Find a model by ID across all providers.

        Args:
            model_id: The model ID to search for

        Returns:
            Tuple of (provider_id, Model) if found, (None, None) otherwise
        """
        providers = self._fetch_providers()

        for provider_id, provider in providers.all.items():
            if model_id in provider.models:
                return provider_id, provider.models[model_id]

        return None, None

    def list_text_capable_models(self, connected_only: bool = True) -> dict[str, list]:
        """Get all models capable of text input/output.

        Args:
            connected_only: If True, only search connected providers (default: True)

        Returns:
            Dict mapping provider_id to list of text-capable models
        """
        providers = self._fetch_providers()

        result = {}
        for provider_id, provider in providers.all.items():
            if connected_only and not providers.is_connected(provider_id):
                continue

            models = provider.list_text_capable_models()
            if models:
                result[provider_id] = models

        return result

    def is_provider_connected(self, provider_id: str) -> bool:
        """Check if a provider is currently connected.

        Args:
            provider_id: The provider ID

        Returns:
            True if connected, False otherwise
        """
        providers = self._fetch_providers()
        return providers.is_connected(provider_id)

    def refresh_cache(self) -> None:
        """Refresh the provider cache."""
        self._cache = None
        self._fetch_providers(use_cache=False)
