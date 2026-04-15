## ADDED Requirements

### Requirement: Retry Configuration Dataclass
The system SHALL provide a `RetryConfig` dataclass to configure exponential backoff retry behavior.

#### Scenario: Create retry config with all parameters
- **WHEN** user creates `RetryConfig(max_retries=5, initial_delay=1.0, max_delay=60.0, exponential_base=2.5)`
- **THEN** config object is created with specified parameters

#### Scenario: Create retry config with defaults
- **WHEN** user creates `RetryConfig()` without parameters
- **THEN** config has sensible defaults: max_retries=3, initial_delay=0.5, max_delay=30.0, exponential_base=2.0

#### Scenario: RetryConfig is immutable
- **WHEN** user attempts to modify a RetryConfig field after creation
- **THEN** modification raises an error (frozen dataclass)

### Requirement: Server Configuration Dataclass
The system SHALL provide a `ServerConfig` dataclass to specify OpenCode server connection details.

#### Scenario: Create server config with basic auth
- **WHEN** user creates `ServerConfig(base_url="http://localhost:5000", basic_auth="dXNlcjpwYXNz")`
- **THEN** config object is created with provided credentials

#### Scenario: Create server config without auth
- **WHEN** user creates `ServerConfig(base_url="http://localhost:5000")`
- **THEN** config object is created; basic_auth defaults to None

#### Scenario: Create server config with custom timeout
- **WHEN** user creates `ServerConfig(base_url="...", timeout=120.0)`
- **THEN** config uses specified timeout value for all requests

#### Scenario: ServerConfig is immutable
- **WHEN** user attempts to modify a ServerConfig field after creation
- **THEN** modification raises an error (frozen dataclass)

### Requirement: Configurable Retry Behavior
The system SHALL allow retry parameters to be customized per-client.

#### Scenario: Different clients with different retry strategies
- **WHEN** user creates two clients: one with max_retries=1, another with max_retries=5
- **THEN** each client uses its configured retry strategy independently

#### Scenario: Retry config persists across requests
- **WHEN** user makes multiple requests with the same client
- **THEN** all requests use the same retry configuration

### Requirement: Exponential Backoff Formula Validation
The system SHALL validate that exponential_base is valid.

#### Scenario: Valid exponential base
- **WHEN** user creates `RetryConfig(exponential_base=2.0)`
- **THEN** config is created successfully

#### Scenario: Exponential base must be > 1.0
- **WHEN** user attempts `RetryConfig(exponential_base=0.5)`
- **THEN** ValueError is raised
