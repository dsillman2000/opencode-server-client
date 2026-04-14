"""Core experiment orchestrator with MLflow integration."""

import concurrent.futures
import hashlib
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Optional

import httpx
import mlflow
import mlflow.entities
from mlflow.entities import SpanEvent
from mlflow.tracing.fluent import with_active_span

from .client import create_http_client
from .config import ExperimentConfig, no_retry_policy
from .io import append_log
from .session import TempOpencodeSession
from .types import (
    ChatTurnTimeout,
    ExperimentResult,
    RetryDecision,
    SessionContext,
    SessionSetupConfig,
)


class OpencodeExperiment:
    """Orchestrates parallel experiment execution with MLflow integration.

    Features:
    - Independent session failure handling
    - Configurable retry logic with custom prompt injection
    - Custom session setup per task
    - MLflow trace hierarchy: top-level experiment trace > session spans
    - Manual polling for chat turn timeouts
    """

    def __init__(self, config: ExperimentConfig):
        """Initialize experiment runner.

        Args:
            config: Experiment configuration
        """
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self._created_session_ids: set[str] = set()
        self._created_session_ids_lock = threading.Lock()

    @staticmethod
    def _add_span_event(
        span: mlflow.entities.LiveSpan,
        name: str,
        attributes: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add a structured event to an MLflow span."""
        span.add_event(SpanEvent(name=name, attributes=attributes or {}))

    @staticmethod
    def _build_workspace_file_content_params(
        workspace_dir: Optional[Path],
        file_path: str,
    ) -> dict[str, str]:
        """Build query params for the Opencode file content API."""
        path = Path(file_path)
        if path.is_absolute():
            return {
                "path": path.name,
                "directory": str(path.parent),
            }

        if workspace_dir is None:
            return {"path": file_path}

        return {
            "path": file_path,
            "directory": str(workspace_dir),
        }

    def _capture_workspace_files(
        self,
        client: httpx.Client,
        workspace_dir: Optional[Path],
        session_idx: int,
    ) -> dict[str, Any]:
        """Capture configured workspace files through the Opencode file content API."""
        captured_files: dict[str, Any] = {}

        for file_path in self.config.workspace_files_to_capture:
            params = self._build_workspace_file_content_params(workspace_dir, file_path)
            try:
                resp = client.get("/file/content", params=params)
                resp.raise_for_status()
                captured_files[file_path] = resp.json()
            except Exception as exc:
                self._log_message(
                    session_idx,
                    f"Workspace file capture failed for {file_path}: {type(exc).__name__}: {exc}",
                )
                captured_files[file_path] = {"error": str(exc), **params}

        return captured_files

    def _register_created_session(self, session_id: str) -> None:
        """Track a created session for shutdown-time polling."""
        with self._created_session_ids_lock:
            self._created_session_ids.add(session_id)

    def _list_created_sessions(self) -> list[str]:
        """Return a stable snapshot of all created session IDs."""
        with self._created_session_ids_lock:
            return list(self._created_session_ids)

    @staticmethod
    def _extract_session_status(payload: Any) -> Optional[str]:
        """Extract a normalized session status from a session payload."""
        if isinstance(payload, dict):
            for key in ("status", "state"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip().lower()

            session_value = payload.get("session")
            if session_value is not None:
                nested_status = OpencodeExperiment._extract_session_status(session_value)
                if nested_status:
                    return nested_status

            data_value = payload.get("data")
            if data_value is not None:
                nested_status = OpencodeExperiment._extract_session_status(data_value)
                if nested_status:
                    return nested_status

        return None

    @staticmethod
    def _session_status_is_running(status: Optional[str]) -> bool:
        """Return whether a normalized session status indicates active work."""
        if status is None:
            return False

        return status in {
            "running",
            "in_progress",
            "in-progress",
            "processing",
            "active",
            "busy",
            "pending",
            "queued",
            "started",
        }

    def _abort_running_sessions_before_termination(
        self,
        root_span: mlflow.entities.LiveSpan,
    ) -> None:
        """Poll all created sessions and abort any still running."""
        session_ids = self._list_created_sessions()
        if not session_ids:
            return

        self._add_span_event(root_span, "experiment_shutdown_poll_started", {"session_count": len(session_ids)})

        client = create_http_client(
            self.config.server.base_url,
            self.config.server.basic_auth,
            gateway_retry_attempts=self.config.gateway_retry_attempts,
            gateway_retry_delay_seconds=self.config.gateway_retry_delay_seconds,
        )
        with client:
            for session_id in session_ids:
                try:
                    resp = client.get(f"/session/{session_id}")
                    if resp.status_code == 404:
                        self._add_span_event(
                            root_span,
                            "experiment_shutdown_poll_session_missing",
                            {"session_id": session_id},
                        )
                        continue

                    resp.raise_for_status()
                    status = self._extract_session_status(resp.json())
                    self._add_span_event(
                        root_span,
                        "experiment_shutdown_polled_session",
                        {"session_id": session_id, "status": status or "unknown"},
                    )

                    if not self._session_status_is_running(status):
                        continue

                    self._add_span_event(
                        root_span,
                        "experiment_shutdown_abort_requested",
                        {"session_id": session_id, "status": status},
                    )
                    abort_resp = client.post(f"/session/{session_id}/abort")
                    abort_resp.raise_for_status()
                    self._add_span_event(
                        root_span,
                        "experiment_shutdown_abort_completed",
                        {"session_id": session_id},
                    )
                except Exception as exc:
                    self._add_span_event(
                        root_span,
                        "experiment_shutdown_poll_failed",
                        {"session_id": session_id, "error": str(exc), "error_type": type(exc).__name__},
                    )

    def run(
        self,
        task_func: Callable[[SessionContext], Any],
        session_setup_factory: Optional[Callable[[int], SessionSetupConfig]] = None,
    ) -> list[ExperimentResult]:
        """Execute the experiment with top-level MLflow trace.

        Args:
            task_func: User-defined task function that takes SessionContext
            session_setup_factory: Optional factory for custom session setup per session

        Returns:
            List of ExperimentResult objects (also recorded in MLflow trace outputs)
        """
        # Create top-level experiment trace
        with mlflow.start_span(name="experiment") as root_span:
            root_span.set_attributes(
                {
                    "experiment_name": self.config.mlflow_experiment_name,
                    "parallel_session_count": self.config.parallel_session_count,
                    "max_active_sessions": self.config.max_active_session_count,
                    "chat_turn_timeout_seconds": self.config.chat_turn_timeout_seconds,
                }
            )
            self._add_span_event(root_span, "experiment_started")

            results: list[ExperimentResult] = []

            # ThreadPoolExecutor for parallel session execution
            with ThreadPoolExecutor(max_workers=self.config.max_active_session_count) as executor:
                futures = {
                    executor.submit(
                        self._run_session_with_retries,
                        root_span,
                        session_idx,
                        task_func,
                        session_setup_factory,
                    ): session_idx
                    for session_idx in range(self.config.parallel_session_count)
                }

                # Process completed futures as they finish
                for future in concurrent.futures.as_completed(futures):
                    session_idx = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        # Log but don't crash - individual session failure is isolated
                        results.append(
                            ExperimentResult(
                                session_id="unknown",
                                model="unknown",
                                prompt_hash="unknown",
                                workspace_directory=None,
                                output=None,
                                status="ERROR",
                                error=str(e),
                            )
                        )

            self._abort_running_sessions_before_termination(root_span)
            self._add_span_event(root_span, "experiment_completed")
            root_span.set_status(mlflow.entities.SpanStatusCode.OK)

            # Record results on the root span so they are captured in the trace.
            result_dicts = [r.to_dict() for r in results]
            root_span.set_outputs(result_dicts)

        return results

    def _run_session_with_retries(
        self,
        root_span: mlflow.entities.LiveSpan,
        session_idx: int,
        task_func: Callable[[SessionContext], Any],
        session_setup_factory: Optional[Callable[[int], SessionSetupConfig]],
    ) -> ExperimentResult:
        """Run a single session with retry logic as a span under root trace.

        Args:
            root_span: Active experiment span to parent this session under
            session_idx: Index of this session (0-based)
            task_func: User task function
            session_setup_factory: Optional session setup factory

        Returns:
            ExperimentResult with outcome
        """
        # Sample prompt and model
        prompt = self.config.prompt_sampler(session_idx)
        model = self.config.model_sampler(session_idx)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

        # Get session setup config
        setup_config = session_setup_factory(session_idx) if session_setup_factory else SessionSetupConfig()

        # MLflow does not propagate span context across threads, so explicitly
        # parent each worker span to the experiment span and make it active in-thread.
        session_span = mlflow.start_span_no_context(
            name=f"session_{uuid.uuid4().hex}",
            span_type="CHAT_MODEL",
            parent_span=root_span,
            attributes={
                "session_index": session_idx,
                "model": model,
                "prompt_hash": prompt_hash,
            },
        )

        session_id: Optional[str] = None
        workspace_dir: Optional[Path] = None
        project_dir: Optional[Path] = None
        output: Any = None
        final_status = "OK"
        final_error: Optional[str] = None
        workspace_files: dict[str, Any] = {}
        start_time = time.time()

        try:
            with with_active_span(session_span):
                try:
                    # Create HTTP client for this session
                    client = create_http_client(
                        self.config.server.base_url,
                        self.config.server.basic_auth,
                        gateway_retry_attempts=self.config.gateway_retry_attempts,
                        gateway_retry_delay_seconds=self.config.gateway_retry_delay_seconds,
                    )

                    # Create session context
                    with client:
                        try:
                            with TempOpencodeSession(
                                client,
                                use_worktree=setup_config.use_worktree,
                                directory=setup_config.directory,
                                create_workspace=setup_config.create_workspace,
                                workspace_creation_spacing_seconds=self.config.workspace_creation_spacing_seconds,
                                logger=lambda msg: self._log_message(session_idx, msg),
                            ) as session_info:
                                session_id = session_info["id"]
                                workspace_dir = Path(session_info["directory"])
                                project_dir = Path(session_info["project_directory"])
                                self._register_created_session(session_id)

                                session_span.set_attribute("session_id", session_id)
                                if session_info.get("branch"):
                                    session_span.set_attribute("worktree_branch", session_info["branch"])
                                self._add_span_event(session_span, "session_created")

                                # Retry loop
                                current_prompt = prompt
                                retry_policy = self.config.retry_policy or no_retry_policy

                                for attempt in range(1, self.config.max_retries_per_session + 2):
                                    with mlflow.start_span(
                                        name=f"chat_{uuid.uuid4().hex}",
                                        span_type="LLM",
                                        attributes={
                                            "session_index": session_idx,
                                            "attempt": attempt,
                                            "model": model,
                                            "prompt_hash": hashlib.sha256(current_prompt.encode()).hexdigest(),
                                        },
                                    ) as turn_span:
                                        turn_span.set_inputs({"prompt": current_prompt})
                                        self._add_span_event(
                                            session_span,
                                            f"attempt_{attempt}_started",
                                        )

                                        try:
                                            # Create context for this attempt
                                            ctx = SessionContext(
                                                session_id=session_id,
                                                model=model,
                                                prompt=current_prompt,
                                                workspace_directory=workspace_dir,
                                                attempt=attempt,
                                                chat_turn_timeout_seconds=self.config.chat_turn_timeout_seconds,
                                                logger=lambda msg: self._log_message(session_idx, msg),
                                                client=client,
                                            )

                                            # Run user task
                                            output = task_func(ctx)
                                            turn_outputs = {"task_output": output}
                                            if ctx.last_chat_turn_output is not None:
                                                turn_outputs.update(ctx.last_chat_turn_output)
                                            turn_span.set_outputs(turn_outputs)
                                            turn_span.set_status(mlflow.entities.SpanStatusCode.OK)

                                            self._add_span_event(
                                                session_span,
                                                f"attempt_{attempt}_completed",
                                                {"status": "success"},
                                            )
                                            break  # Success, exit retry loop

                                        except Exception as e:
                                            error_message = f"Attempt {attempt} failed: {type(e).__name__}: {e}"
                                            self._log_message(session_idx, error_message)
                                            turn_span.set_status(mlflow.entities.SpanStatusCode.ERROR)
                                            self._add_span_event(
                                                turn_span,
                                                "turn_failed",
                                                {"error": str(e), "error_type": type(e).__name__},
                                            )
                                            self._add_span_event(
                                                session_span,
                                                f"attempt_{attempt}_failed",
                                                {"error": str(e), "error_type": type(e).__name__},
                                            )

                                            # Check retry policy
                                            retry_decision = retry_policy(attempt, e, ctx)

                                            if (
                                                retry_decision.should_retry
                                                and attempt < self.config.max_retries_per_session + 1
                                            ):
                                                current_prompt = retry_decision.custom_prompt or prompt
                                                self._add_span_event(
                                                    turn_span,
                                                    "retry_decision",
                                                    {"reason": retry_decision.reason},
                                                )
                                                self._add_span_event(
                                                    session_span,
                                                    "retry_decision",
                                                    {"reason": retry_decision.reason},
                                                )
                                                self._log_message(
                                                    session_idx,
                                                    f"Retry decision: {retry_decision.reason}",
                                                )
                                            else:
                                                final_error = str(e)
                                                final_status = "ERROR"
                                                raise  # Will be caught by outer try/except
                        finally:
                            workspace_files = self._capture_workspace_files(client, workspace_dir, session_idx)
                            # Cleanup resources while the HTTP client is still open.
                            self._cleanup_session_resources(
                                client=client,
                                session_idx=session_idx,
                                session_id=session_id,
                                workspace_dir=workspace_dir,
                                project_dir=project_dir,
                                use_worktree=setup_config.use_worktree,
                            )

                except Exception as e:
                    final_status = "ERROR"
                    final_error = str(e)
                    self._log_message(session_idx, f"Session failed: {type(e).__name__}: {e}")

                # Record session result
                execution_time = time.time() - start_time
                session_span.set_outputs(
                    {
                        "task_output": output,
                        "workspace_files": workspace_files,
                        "status": final_status,
                        "error": final_error,
                    }
                )
                session_span.set_status(
                    mlflow.entities.SpanStatusCode.OK if final_status == "OK" else mlflow.entities.SpanStatusCode.ERROR
                )

                return ExperimentResult(
                    session_id=session_id or "unknown",
                    model=model,
                    prompt_hash=prompt_hash,
                    workspace_directory=workspace_dir,
                    output=output,
                    status=final_status,
                    error=final_error,
                    execution_time_seconds=execution_time,
                )
        finally:
            session_span.end()

    def _log_message(self, session_idx: int, message: str) -> None:
        """Log a message to the session's log file.

        Args:
            session_idx: Session index
            message: Message to log
        """
        log_path = self.config.output_dir / f"session_{session_idx:03d}.log"
        append_log(log_path, message)

    def _cleanup_session_resources(
        self,
        client: httpx.Client,
        session_idx: int,
        session_id: Optional[str],
        workspace_dir: Optional[Path],
        project_dir: Optional[Path],
        use_worktree: bool,
    ) -> None:
        """Cleanup session and worktree resources according to config.

        Args:
            client: HTTP client
            session_idx: Session index for logging
            session_id: Session ID to delete if configured
            workspace_dir: Worktree directory to delete if configured
            project_dir: Project directory associated with the worktree
            use_worktree: Whether this session created a worktree
        """
        if self.config.clean_up_sessions and session_id:
            try:
                self._cleanup_session(client, session_id)
            except Exception as cleanup_err:
                self._log_message(session_idx, f"Session cleanup error: {cleanup_err}")

        if self.config.clean_up_worktrees and use_worktree and workspace_dir and project_dir:
            try:
                self._cleanup_worktree(client, project_dir, workspace_dir)
            except Exception as cleanup_err:
                self._log_message(session_idx, f"Worktree cleanup error: {cleanup_err}")

    def _cleanup_session(self, client: httpx.Client, session_id: str) -> None:
        """Cleanup a session by deleting it.

        Args:
            client: HTTP client
            session_id: Session ID to delete
        """
        resp = client.delete(f"/session/{session_id}")
        resp.raise_for_status()

    def _cleanup_worktree(
        self,
        client: httpx.Client,
        project_directory: Path,
        worktree_directory: Path,
    ) -> None:
        """Cleanup a worktree by deleting its directory through the API.

        Args:
            client: HTTP client
            project_directory: Original project directory used to create the worktree
            worktree_directory: Worktree directory to delete
        """
        payload = {"directory": str(worktree_directory)}
        print("Deleting worktree at", worktree_directory)
        print("Project directory for cleanup:", project_directory)
        resp = client.request(
            "DELETE",
            "/experimental/worktree",
            params={"directory": str(project_directory)},
            json=payload,
        )
        resp.raise_for_status()
