"""mlflow_opencode - High-Level API for Parallel Opencode Experiments

A Python module that provides a clean, ergonomic interface for running parallel
agentic tasks on Opencode servers with MLflow integration.

## Features

- **Parallel Execution**: Run multiple sessions concurrently with configurable
  concurrency limits
- **Error Resilience**: Individual session failures don't crash the experiment;
  each result is tracked independently
- **Retry Logic**: Configurable retry policies with custom prompt injection
  (e.g., "retry" behavior on timeout)
- **Custom Session Setup**: Per-session customization (worktrees, directories)
- **MLflow Integration**: Hierarchical trace structure (top-level experiment trace
  > session spans) with automatic result tracking
- **Chat Turn Timeouts**: Manual polling-based timeout detection for agent
  reasoning steps
- **Sampling**: Flexible prompt and model sampling strategies

## Architecture

```
src/mlflow_opencode/
├── types.py          # Core data structures and type definitions
├── config.py         # Configuration classes and retry policies
├── client.py         # HTTP client setup and provider queries
├── session.py        # Session management (optionally with worktrees)
├── streaming.py      # Streaming prompt execution
├── samplers.py       # Sampler factory functions
├── io.py             # Logging and artifact utilities
├── experiment.py     # Main orchestrator with MLflow integration
└── __init__.py       # Public API exports
```

## Quick Start

### Basic SVG Generation Example

```python
from src.mlflow_opencode import (
    ExperimentConfig,
    OpencodeServerConfig,
    OpencodeExperiment,
    SessionContext,
    ValidationError,
    samplers,
    timeout_with_retry_policy,
)

def svg_task(ctx: SessionContext) -> str:
    \"\"\"Your task function - receives context with session info.\"\"\"
    response = ctx.run_prompt()
    svg = normalize_svg_response(response)
    is_valid, error = validate_svg_document(svg)
    if not is_valid:
        raise ValidationError(f"Invalid SVG: {error}")
    return svg

# Configuration
config = ExperimentConfig(
    server=OpencodeServerConfig(
        base_url="http://opencode.dsillman.com",
        basic_auth=os.getenv("BASIC_CREDS"),
    ),
    mlflow_tracking_uri="http://localhost:5000",
    mlflow_experiment_name="svg-generation",
    parallel_session_count=8,
    max_active_session_count=4,
    chat_turn_timeout_seconds=90,
    output_dir=Path("./output"),
    prompt_sampler=samplers.constant_sampler("Draw an SVG of a cat"),
    model_sampler=samplers.from_list_sampler(["model1", "model2"]),
    retry_policy=timeout_with_retry_policy,
)

# Run experiment
exp = OpencodeExperiment(config)
results = exp.run(svg_task)

# Results are: List[ExperimentResult]
# Each result contains: session_id, model, prompt_hash, output, status, error
```

### With Custom Session Setup (Worktrees)

```python
from src.mlflow_opencode import SessionSetupConfig

def custom_session_setup(session_idx: int) -> SessionSetupConfig:
    \"\"\"Customize each session (e.g., enable worktree).\"\"\"
    return SessionSetupConfig(
        use_worktree=True,
        directory=Path(__file__).parent,
        create_workspace=True,
    )

config = ExperimentConfig(
    # ... other fields ...
    session_setup_factory=custom_session_setup,
)

exp = OpencodeExperiment(config)
results = exp.run(my_task, session_setup_factory=custom_session_setup)
```

## Core Components

### SessionContext

Passed to your task function. Provides:

```python
@dataclass
class SessionContext:
    session_id: str                    # Unique session ID
    model: str                         # Model being used
    prompt: str                        # Current prompt (may be overridden by retry)
    workspace_directory: Optional[Path] # If using worktree
    attempt: int                       # Current attempt number (1-indexed)
    logger: Callable[[str], None]      # Log function
    client: httpx.Client               # Low-level HTTP client
    
    def run_prompt(self) -> str:
        """Execute the prompt and get response."""
```

### ExperimentResult

Returned from `exp.run()`. Contains:

```python
@dataclass
class ExperimentResult:
    session_id: str
    model: str
    prompt_hash: str                   # SHA256 of original prompt
    workspace_directory: Optional[Path]
    output: Any                        # User-defined output from task
    status: str                        # "OK" or "ERROR"
    error: Optional[str]               # Error message if failed
    execution_time_seconds: float
```

### Retry Policies

Control what happens when a session fails:

```python
# No retries - fail on first error
from src.mlflow_opencode import no_retry_policy

# Retry on timeout with configurable attempt limit
from src.mlflow_opencode import timeout_retry_policy

retry_policy = timeout_retry_policy(max_timeout_attempts=3)

# Custom policy
def my_retry_policy(attempt: int, error: Exception, ctx: SessionContext) -> RetryDecision:
    if attempt < 3 and isinstance(error, SomeError):
        return RetryDecision(
            should_retry=True,
            custom_prompt="Please retry with more care...",
            reason="Retrying after error"
        )
    return RetryDecision(should_retry=False)

config = ExperimentConfig(
    # ...
    retry_policy=my_retry_policy,
    max_retries_per_session=2,
)
```

### Samplers

Define how prompts and models are selected:

```python
from src.mlflow_opencode import samplers

# Same prompt/model for all sessions
samplers.constant_sampler("prompt text")
samplers.constant_sampler("model-id")

# Cycle through list
samplers.from_list_sampler(["prompt1", "prompt2"])
samplers.from_list_sampler(["model1", "model2"])

# Random selection
samplers.random_sampler(["option1", "option2"])

# Custom function
def my_model_selector(session_idx: int) -> str:
    return "model1" if session_idx % 2 == 0 else "model2"
samplers.index_based_sampler(my_model_selector)
```

## MLflow Integration

The module creates a hierarchical trace structure:

```
Experiment Trace (top-level)
├── attributes: experiment_name, config
├── events: experiment_started, experiment_completed
│
└── Session Spans (one per session, concurrent)
    ├── Session 0 Span
    │   ├── attributes: session_id, model, prompt_hash
    │   ├── events: session_created, attempt_1_started, attempt_1_completed
    │   └── status: OK
    │
    ├── Session 1 Span
    │   ├── events: session_created, attempt_1_failed, retry_decision, attempt_2_started
    │   └── status: OK
    │
    └── ...

Results: List[ExperimentResult] → recorded as trace outputs
```

## Error Handling & Resilience

- **Independent Session Failures**: One session's crash doesn't affect others
- **Retry Injection**: Custom prompts can be injected for retry attempts
- **Timeout Detection**: Manual polling detects when agent turns exceed
  `chat_turn_timeout_seconds`
- **Result Tracking**: Each result's status shows outcome (OK, ERROR, etc.)

## Configuration

```python
@dataclass(frozen=True)
class ExperimentConfig:
    # Connection
    server: OpencodeServerConfig
    
    # MLflow
    mlflow_tracking_uri: str
    mlflow_experiment_name: str
    
    # Execution
    parallel_session_count: int        # Total sessions
    max_active_session_count: int      # Max concurrent
    chat_turn_timeout_seconds: int     # Timeout per turn
    
    # I/O
    output_dir: Path
    
    # Sampling
    prompt_sampler: PromptSampler
    model_sampler: ModelSampler
    
    # Error handling
    retry_policy: Optional[RetryPolicy] = None
    max_retries_per_session: int = 1
    gateway_retry_attempts: int = 2
    gateway_retry_delay_seconds: float = 0.5
    
    # Session customization
    session_setup_factory: Optional[SessionSetupFactory] = None
    workspace_files_to_capture: list[str] = field(default_factory=list)
    
    # Cleanup
    clean_up_sessions: bool = True
    clean_up_worktrees: bool = True
```

## API Reference

### Main Class

- `OpencodeExperiment(config: ExperimentConfig)` - Create experiment runner
  - `.run(task_func, session_setup_factory=None) -> List[ExperimentResult]`

### Configuration

- `ExperimentConfig` - Full configuration dataclass
- `OpencodeServerConfig` - Server connection details
- `SessionSetupConfig` - Per-session customization

### Data Types

- `SessionContext` - Context passed to task functions
- `ExperimentResult` - Result from each session
- `RetryDecision` - Return type from retry policies
- `ChatTurnTimeout` - Exception for timeout errors
- `ValidationError` - Exception for validation failures

### Utilities

- `samplers.constant_sampler(value)`
- `samplers.from_list_sampler(values)`
- `samplers.random_sampler(values)`
- `samplers.index_based_sampler(func)`
- `retry_policies.no_retry_policy`
- `retry_policies.timeout_with_retry_policy`
- `retry_policies.always_retry_policy`
- `append_log(log_path, message)` - Log to file
- `write_json_artifact(payload, prefix)` - Write JSON artifact

## File Organization

Sessions produce logs and outputs in `config.output_dir`:

```
output/
├── session_000.log     # Session 0 log file
├── session_001.log     # Session 1 log file
└── ...
```

Each log contains timestamped messages about that session's execution.

## Notes

- All operations use threading (no async/await)
- Results are returned as in-memory list and also stored in MLflow trace
- Session cleanup can be controlled via `clean_up_sessions` config
- Worktree cleanup can be controlled via `clean_up_worktrees` config
- Session span outputs can include arbitrary workspace files via `workspace_files_to_capture`
- Prompts are hashed (SHA256) in results for tracking
- Execution time is tracked per session
"""
