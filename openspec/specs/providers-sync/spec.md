# Provider Management (Sync) Specification

## Purpose

Manage providers and models from the OpenCode server. Provides user-friendly APIs for querying available providers, their models, and filtering by capabilities.

## Requirements

### Requirement: List All Providers
The system SHALL allow users to list all available providers.

#### Scenario: List all providers
- **WHEN** user calls `ProviderManager.list_providers()`
- **THEN** system returns list of all Provider objects from `/provider`

#### Scenario: List connected only
- **WHEN** user calls `list_providers(connected_only=True)`
- **THEN** system returns only providers marked as connected

#### Scenario: Providers includes models
- **WHEN** user lists providers
- **THEN** each Provider includes its available models

### Requirement: Get Provider by ID
The system SHALL allow users to retrieve a specific provider.

#### Scenario: Get existing provider
- **WHEN** user calls `ProviderManager.get_provider("deepseek")`
- **THEN** system returns Provider object with models

#### Scenario: Get non-existent provider
- **WHEN** user calls `get_provider("unknown")`
- **THEN** system returns None

### Requirement: Get Model from Provider
The system SHALL allow users to retrieve a specific model from a provider.

#### Scenario: Get existing model
- **WHEN** user calls `ProviderManager.get_model("deepseek", "deepseek-chat")`
- **THEN** system returns Model object

#### Scenario: Get non-existent model
- **WHEN** user calls `get_model("deepseek", "unknown")`
- **THEN** system returns None

### Requirement: Find Model Across Providers
The system SHALL allow users to search for a model across all providers.

#### Scenario: Find model
- **WHEN** user calls `ProviderManager.find_model("gpt-4")`
- **THEN** system returns tuple of (provider_id, Model) or (None, None)

#### Scenario: Model not found
- **WHEN** user calls `find_model("unknown-model")`
- **THEN** system returns (None, None)

### Requirement: List Text-Capable Models
The system SHALL allow users to find models that support text input/output.

#### Scenario: List text-capable from connected
- **WHEN** user calls `list_text_capable_models(connected_only=True)`
- **THEN** system returns dict mapping provider_id to text-capable models

#### Scenario: List text-capable all
- **WHEN** user calls `list_text_capable_models(connected_only=False)`
- **THEN** system includes models from disconnected providers

### Requirement: Check Provider Connection
The system SHALL allow users to check if a provider is currently connected.

#### Scenario: Provider connected
- **WHEN** user calls `is_provider_connected("openai")`
- **THEN** system returns True if in connected list

#### Scenario: Provider disconnected
- **WHEN** user calls `is_provider_connected("nvidia")`
- **THEN** system returns False if not in connected list

### Requirement: Cache Management
The system SHALL cache provider data for efficiency.

#### Scenario: Cache reused
- **WHEN** user calls multiple methods
- **THEN** system caches and reuses `/provider` response

#### Scenario: Refresh cache
- **WHEN** user calls `refresh_cache()`
- **THEN** system clears cache and refetches