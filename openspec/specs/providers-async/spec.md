# Provider Management (Async) Specification

> **NOTE**: This is the async version of the providers-sync specification.

## Purpose

Manage providers and models from the OpenCode server asynchronously. Provides user-friendly APIs for querying available providers, their models, and filtering by capabilities.

## Requirements

### Requirement: Async List All Providers
The system SHALL allow users to asynchronously list all available providers.

#### Scenario: List all providers with await
- **WHEN** user awaits `AsyncProviderManager.list_providers()`
- **THEN** coroutine returns list of all Provider objects from `/provider`

#### Scenario: List connected only with await
- **WHEN** user awaits `list_providers(connected_only=True)`
- **THEN** coroutine returns only providers marked as connected

#### Scenario: Providers includes models
- **WHEN** user lists providers
- **THEN** each Provider includes its available models

### Requirement: Async Get Provider by ID
The system SHALL allow users to asynchronously retrieve a specific provider.

#### Scenario: Get existing provider with await
- **WHEN** user awaits `AsyncProviderManager.get_provider("deepseek")`
- **THEN** coroutine returns Provider object with models

#### Scenario: Get non-existent provider with await
- **WHEN** user awaits `get_provider("unknown")`
- **THEN** coroutine returns None

### Requirement: Async Get Model from Provider
The system SHALL allow users to asynchronously retrieve a specific model from a provider.

#### Scenario: Get existing model with await
- **WHEN** user awaits `AsyncProviderManager.get_model("deepseek", "deepseek-chat")`
- **THEN** coroutine returns Model object

#### Scenario: Get non-existent model with await
- **WHEN** user awaits `get_model("deepseek", "unknown")`
- **THEN** coroutine returns None

### Requirement: Async Find Model Across Providers
The system SHALL allow users to asynchronously search for a model across all providers.

#### Scenario: Find model with await
- **WHEN** user awaits `AsyncProviderManager.find_model("gpt-4")`
- **THEN** coroutine returns tuple of (provider_id, Model) or (None, None)

#### Scenario: Model not found with await
- **WHEN** user awaits `find_model("unknown-model")`
- **THEN** coroutine returns (None, None)

### Requirement: Async List Text-Capable Models
The system SHALL allow users to asynchronously find models that support text input/output.

#### Scenario: List text-capable from connected with await
- **WHEN** user awaits `list_text_capable_models(connected_only=True)`
- **THEN** coroutine returns dict mapping provider_id to text-capable models

#### Scenario: List text-capable all with await
- **WHEN** user awaits `list_text_capable_models(connected_only=False)`
- **THEN** coroutine includes models from disconnected providers

### Requirement: Async Check Provider Connection
The system SHALL allow users to asynchronously check if a provider is connected.

#### Scenario: Provider connected with await
- **WHEN** user awaits `is_provider_connected("openai")`
- **THEN** coroutine returns True if in connected list

#### Scenario: Provider disconnected with await
- **WHEN** user awaits `is_provider_connected("nvidia")`
- **THEN** coroutine returns False if not in connected list

### Requirement: Async Cache Management
The system SHALL cache provider data for efficiency.

#### Scenario: Cache reused with await
- **WHEN** user awaits multiple methods
- **THEN** coroutine caches and reuses `/provider` response

#### Scenario: Refresh cache with await
- **WHEN** user awaits `refresh_cache()`
- **THEN** coroutine clears cache and refetches