"""I/O utilities for logging and artifact management."""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any


def append_log(log_path: Path, message: str) -> None:
    """Append a timestamped message to a log file.
    
    Args:
        log_path: Path to log file
        message: Message to append
    """
    timestamp = time.strftime("%H:%M:%S")
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def write_json_artifact(payload: Any, prefix: str, suffix: str = ".json") -> Path:
    """Write a JSON artifact to a temporary file.
    
    Args:
        payload: Object to serialize as JSON
        prefix: Prefix for temporary file
        suffix: Suffix for temporary file (default: ".json")
        
    Returns:
        Path to created file
    """
    fd, path_str = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(fd)
    path = Path(path_str)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
