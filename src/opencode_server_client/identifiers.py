"""OpenCode-style monotonic identifier generation.

This module mirrors the native JavaScript identifier behavior used by
OpenCode so that client-generated IDs for messages and parts follow the
same shape and ordering characteristics.
"""

from __future__ import annotations

import secrets
import threading
import time

_BASE62_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_DEFAULT_ID_LENGTH = 26
_TIME_MASK_48_BITS = (1 << 48) - 1
_state_lock = threading.Lock()
_last_timestamp = 0
_counter = 0


def _random_base62(length: int) -> str:
    """Generate a random base62 string of the requested length."""
    if length <= 0:
        return ""

    random_bytes = secrets.token_bytes(length)
    return "".join(_BASE62_CHARS[b % 62] for b in random_bytes)


def generate_new_id(
    length: int = _DEFAULT_ID_LENGTH,
    *,
    descending: bool = False,
    timestamp: int | None = None,
) -> str:
    """Generate an OpenCode-style monotonic ID body.

    The returned value does not include a resource prefix such as msg_, prt_,
    or ses_. By default it produces a 26-character identifier containing a
    time-derived 12-character hexadecimal prefix plus a random base62 suffix.
    """
    if length < 12:
        raise ValueError("length must be at least 12")

    current_timestamp = int(time.time() * 1000) if timestamp is None else int(timestamp)

    global _last_timestamp, _counter
    with _state_lock:
        if current_timestamp != _last_timestamp:
            _last_timestamp = current_timestamp
            _counter = 0
        _counter += 1
        now_value = current_timestamp * 0x1000 + _counter

    now_value &= _TIME_MASK_48_BITS
    if descending:
        now_value = (~now_value) & _TIME_MASK_48_BITS

    time_prefix = now_value.to_bytes(6, byteorder="big", signed=False).hex()
    return time_prefix + _random_base62(length - len(time_prefix))


def generate_message_id(length: int = _DEFAULT_ID_LENGTH) -> str:
    """Generate a new OpenCode-style message identifier."""
    return f"msg_{generate_new_id(length)}"


def generate_part_id(length: int = _DEFAULT_ID_LENGTH) -> str:
    """Generate a new OpenCode-style message part identifier."""
    return f"prt_{generate_new_id(length)}"


def generate_session_id(length: int = _DEFAULT_ID_LENGTH) -> str:
    """Generate a new OpenCode-style session identifier."""
    return f"ses_{generate_new_id(length)}"
