"""Type definitions for providers and models."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TextCapability:
    """Text capability information."""

    supported: bool


@dataclass
class InputCapabilities:
    """Input capabilities for a model."""

    text: Optional[bool] = None


@dataclass
class OutputCapabilities:
    """Output capabilities for a model."""

    text: Optional[bool] = None


@dataclass
class ModelCapabilities:
    """Complete capabilities for a model."""

    input: Optional[InputCapabilities] = None
    output: Optional[OutputCapabilities] = None
    toolcall: Optional[bool] = None
    reasoning: Optional[bool] = None

    def has_text_io(self) -> bool:
        """Check if model supports text input and output."""
        return (self.input and self.input.text is True) and (
            self.output and self.output.text is True
        )

    def has_toolcall(self) -> bool:
        """Check if model supports tool calls."""
        return self.toolcall is True

    def has_reasoning(self) -> bool:
        """Check if model supports reasoning."""
        return self.reasoning is True


@dataclass
class ModelCost:
    """Pricing information for a model."""

    input: Optional[float] = None
    output: Optional[float] = None


@dataclass
class Model:
    """Model information from the provider."""

    id: str
    capabilities: ModelCapabilities
    cost: Optional[ModelCost] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Model":
        """Create a Model from API response data."""
        capabilities_data = data.get("capabilities", {})
        input_data = capabilities_data.get("input", {})
        output_data = capabilities_data.get("output", {})

        input_caps = InputCapabilities(
            text=input_data.get("text") if isinstance(input_data, dict) else input_data
        )
        output_caps = OutputCapabilities(
            text=output_data.get("text")
            if isinstance(output_data, dict)
            else output_data
        )

        capabilities = ModelCapabilities(
            input=input_caps,
            output=output_caps,
            toolcall=capabilities_data.get("toolcall"),
            reasoning=capabilities_data.get("reasoning"),
        )

        cost_data = data.get("cost", {})
        cost = (
            ModelCost(input=cost_data.get("input"), output=cost_data.get("output"))
            if cost_data
            else None
        )

        return cls(id=data["id"], capabilities=capabilities, cost=cost)


@dataclass
class Provider:
    """Provider information with available models."""

    id: str
    models: Dict[str, Model]

    @classmethod
    def from_dict(cls, provider_id: str, data: dict) -> "Provider":
        """Create a Provider from API response data."""
        models_data = data.get("models", {})
        models = {}

        for model_id, model_data in models_data.items():
            model_data_with_id = {**model_data, "id": model_id}
            models[model_id] = Model.from_dict(model_data_with_id)

        return cls(id=provider_id, models=models)

    def get_model(self, model_id: str) -> Optional[Model]:
        """Get a specific model by ID."""
        return self.models.get(model_id)

    def list_text_capable_models(self) -> list[Model]:
        """Get all models that support text input/output."""
        return [
            model for model in self.models.values() if model.capabilities.has_text_io()
        ]

    def list_models_with_capabilities(
        self,
        text_capable: bool = False,
        toolcall: bool = False,
        reasoning: bool = False,
    ) -> list[Model]:
        """Get models filtered by specific capabilities."""
        filtered = []
        for model in self.models.values():
            if text_capable and not model.capabilities.has_text_io():
                continue
            if toolcall and not model.capabilities.has_toolcall():
                continue
            if reasoning and not model.capabilities.has_reasoning():
                continue
            filtered.append(model)
        return filtered


@dataclass
class ProviderList:
    """List of available providers."""

    all: Dict[str, Provider]
    connected: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderList":
        """Create a ProviderList from API response data.

        Supports either of these API shapes for `all`:
        - {"all": {"openai": {...}, "anthropic": {...}}}
        - {"all": [{"id": "openai", ...}, {"id": "anthropic", ...}]}
        """
        all_providers = {}
        raw_providers = data.get("all", {})

        if isinstance(raw_providers, dict):
            for provider_id, provider_data in raw_providers.items():
                all_providers[provider_id] = Provider.from_dict(
                    provider_id, provider_data
                )
        else:
            for provider_data in raw_providers:
                provider_id = provider_data["id"]
                all_providers[provider_id] = Provider.from_dict(
                    provider_id, provider_data
                )

        connected = data.get("connected", [])

        return cls(all=all_providers, connected=connected)

    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get a specific provider by ID."""
        return self.all.get(provider_id)

    def is_connected(self, provider_id: str) -> bool:
        """Check if a provider is connected."""
        return provider_id in self.connected

    def list_connected_providers(self) -> list[Provider]:
        """Get all connected providers."""
        return [self.all[pid] for pid in self.connected if pid in self.all]
