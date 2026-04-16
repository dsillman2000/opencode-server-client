"""Sync event subscriber for real-time Server-Sent Events (SSE) via background thread.

This module provides the EventSubscriber class which handles subscribing to
the /global/event SSE stream using a background thread. Callbacks are invoked
in the background thread context.

The EventSubscriber:
- Manages background thread for reading SSE stream
- Parses SSE events to typed objects
- Invokes user callbacks for matched events
- Handles reconnection with exponential backoff
- Supports session_id filtering

Typical usage:
    >>> from opencode_server_client.events.sync_subscriber import EventSubscriber
    >>> from opencode_server_client.events.types import SessionIdleEvent
    >>>
    >>> subscriber = EventSubscriber(http_client)
    >>>
    >>> def on_idle(event: SessionIdleEvent):
    ...     print(f"Session {event.session_id} is idle")
    >>>
    >>> subscriber.subscribe(
    ...     session_id_filter="abc123",
    ...     on_idle=on_idle
    ... )
    >>> # ... wait for events ...
    >>> subscriber.close()
"""

import logging
import threading
from typing import Callable, Optional

from opencode_server_client.events.parser import EventParser
from opencode_server_client.events.types import (
    AnyEvent,
    SessionErrorEvent,
    SessionIdleEvent,
)
from opencode_server_client.http_client.sync_client import SyncHttpClient

logger = logging.getLogger(__name__)


class EventSubscriber:
    """Subscribe to real-time events from /global/event SSE stream.

    This class manages a background thread that reads SSE events from the
    server and invokes user callbacks. It supports:
    - Multiple simultaneous subscriptions with different callbacks
    - Session ID filtering (only process events for specific sessions)
    - Automatic reconnection with exponential backoff
    - Graceful shutdown

    Attributes:
        http_client: SyncHttpClient instance for HTTP requests
        _stream_thread: Background thread reading SSE stream (or None)
        _stop_event: Threading event to signal thread to stop
        _subscriptions: Dict of registered callbacks
        _lock: Threading lock for thread-safe operations
    """

    # Initial reconnection delay in seconds
    INITIAL_RECONNECT_DELAY = 1.0
    # Maximum reconnection delay in seconds
    MAX_RECONNECT_DELAY = 30.0
    # Exponential backoff multiplier
    RECONNECT_BASE = 2.0
    # Thread shutdown timeout in seconds
    SHUTDOWN_TIMEOUT = 5.0

    def __init__(self, http_client: SyncHttpClient):
        """Initialize the EventSubscriber.

        Args:
            http_client: SyncHttpClient instance for making requests
        """
        self.http_client = http_client
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._subscriptions = []  # List of (session_id_filter, callbacks_dict)
        self._lock = threading.Lock()
        self._parser = EventParser()
        self._reconnect_attempt = 0

    def subscribe(
        self,
        on_event: Optional[Callable[[AnyEvent], None]] = None,
        on_idle: Optional[Callable[[SessionIdleEvent], None]] = None,
        on_error: Optional[Callable[[SessionErrorEvent], None]] = None,
        session_id_filter: Optional[str] = None,
    ) -> None:
        """Register callbacks for events.

        Callbacks are invoked in the background thread context. Keep callbacks
        quick to avoid blocking the stream.

        Args:
            on_event: Callback for any event type
            on_idle: Callback for SessionIdleEvent only
            on_error: Callback for SessionErrorEvent only
            session_id_filter: Optional session_id to filter events (if provided,
                only events matching this session are processed)

        Example:
            >>> subscriber.subscribe(
            ...     on_idle=lambda e: print(f"Session {e.session_id} idle"),
            ...     session_id_filter="abc123"
            ... )
        """
        with self._lock:
            self._subscriptions.append(
                {
                    "on_event": on_event,
                    "on_idle": on_idle,
                    "on_error": on_error,
                    "session_id_filter": session_id_filter,
                }
            )

            # Start background thread on first subscription
            if self._stream_thread is None or not self._stream_thread.is_alive():
                self._stop_event.clear()
                self._reconnect_attempt = 0
                self._stream_thread = threading.Thread(
                    target=self._read_sse_stream,
                    daemon=True,
                    name="opencode-sse-stream",
                )
                self._stream_thread.start()
                logger.debug("Started SSE stream thread")

    def unsubscribe(self) -> None:
        """Remove all subscriptions and stop the background thread.

        This method stops the background thread and clears all callbacks.
        """
        with self._lock:
            self._subscriptions.clear()
            self._stop_event.set()

    def close(self, timeout: float = SHUTDOWN_TIMEOUT) -> None:
        """Gracefully shutdown the background thread.

        Args:
            timeout: Maximum time to wait for thread to stop (seconds)

        Example:
            >>> subscriber.close(timeout=5.0)
        """
        logger.debug("Closing EventSubscriber")
        self._stop_event.set()

        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=timeout)
            if self._stream_thread.is_alive():
                logger.warning(
                    f"SSE stream thread did not stop within {timeout}s timeout"
                )

    def _read_sse_stream(self) -> None:
        """Background thread: Read SSE stream and dispatch events.

        This method runs in the background thread and:
        1. Connects to /global/event endpoint using http_client.stream()
        2. Reads SSE events using proper SSE parsing
        3. Parses event data using EventParser
        4. Invokes matching callbacks
        5. Handles reconnection on errors
        """
        while not self._stop_event.is_set():
            try:
                self._reconnect_attempt += 1
                logger.debug(
                    f"Connecting to SSE stream (attempt {self._reconnect_attempt})"
                )

                # Use the http_client.stream() method for SSE connection
                with self.http_client.stream("GET", "/global/event") as response:
                    # Check response status
                    response.raise_for_status()

                    # Reset reconnect attempt counter on successful connection
                    self._reconnect_attempt = 0

                    # Read SSE events line by line
                    # We parse the stream manually to handle non-standard Content-Type
                    event_data = {}
                    for line in response.iter_lines():
                        if self._stop_event.is_set():
                            break

                        line = line.strip()
                        if not line:
                            # Empty line signals end of event
                            if event_data.get("data"):
                                try:
                                    # Parse the accumulated event data
                                    event = self._parser.parse(
                                        event_data["data"].encode("utf-8")
                                    )
                                    if event:
                                        self._dispatch_event(event)
                                except Exception as e:
                                    logger.error(f"Error parsing SSE event: {e}")
                            event_data = {}
                            continue

                        # Parse SSE field format: "field: value"
                        if ":" in line:
                            field, value = line.split(":", 1)
                            field = field.strip()
                            value = value.lstrip()  # Remove leading space after colon

                            if field == "data":
                                # Accumulate data lines
                                if "data" in event_data:
                                    event_data["data"] += "\n" + value
                                else:
                                    event_data["data"] = value
                            elif field == "event":
                                event_data["event"] = value
                            elif field == "id":
                                event_data["id"] = value
                            elif field == "retry":
                                event_data["retry"] = value
                        # Skip comments (lines starting with :)

                logger.debug("SSE stream ended normally")

            except Exception as e:
                if self._stop_event.is_set():
                    break

                logger.warning(f"SSE stream error: {e}")

                # Calculate reconnect delay with exponential backoff
                delay = min(
                    self.INITIAL_RECONNECT_DELAY
                    * (self.RECONNECT_BASE ** (self._reconnect_attempt - 1)),
                    self.MAX_RECONNECT_DELAY,
                )

                logger.debug(f"Reconnecting in {delay}s...")

                # Wait for stop event or reconnect delay
                if not self._stop_event.wait(timeout=delay):
                    continue
                else:
                    break

    def _dispatch_event(self, event: AnyEvent) -> None:
        """Dispatch event to matching callbacks.

        Args:
            event: Parsed event object to dispatch
        """
        with self._lock:
            for subscription in self._subscriptions:
                # Check session_id filter
                if subscription.get("session_id_filter"):
                    # Event must have session_id attribute
                    if not hasattr(event, "session_id"):
                        continue
                    if event.session_id != subscription["session_id_filter"]:
                        continue

                # Invoke callbacks
                try:
                    # Generic on_event callback
                    if subscription.get("on_event"):
                        subscription["on_event"](event)

                    # Type-specific callbacks
                    if isinstance(event, SessionIdleEvent) and subscription.get(
                        "on_idle"
                    ):
                        subscription["on_idle"](event)

                    elif isinstance(event, SessionErrorEvent) and subscription.get(
                        "on_error"
                    ):
                        subscription["on_error"](event)

                except Exception as e:
                    logger.error(f"Error in event callback: {e}", exc_info=True)
