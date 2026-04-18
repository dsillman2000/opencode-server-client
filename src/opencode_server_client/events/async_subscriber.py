"""Async event subscriber for real-time Server-Sent Events (SSE) via asyncio tasks.

This module provides the AsyncEventSubscriber class which handles subscribing to
the /global/event SSE stream using asyncio tasks. Callbacks can be either
sync or async functions.

The AsyncEventSubscriber:
- Manages asyncio task for reading SSE stream
- Parses SSE events to typed objects
- Invokes user callbacks for matched events (supports both sync and async callbacks)
- Handles reconnection with exponential backoff
- Supports session_id filtering
- Supports async iterator pattern for event consumption

Typical usage:
    >>> from opencode_server_client.events.async_subscriber import AsyncEventSubscriber
    >>> from opencode_server_client.events.types import SessionIdleEvent
    >>>
    >>> subscriber = AsyncEventSubscriber(http_client)
    >>>
    >>> async def on_idle(event: SessionIdleEvent):
    ...     print(f"Session {event.session_id} is idle")
    >>>
    >>> await subscriber.subscribe(
    ...     session_id_filter="abc123",
    ...     on_idle=on_idle
    ... )
    >>> # ... wait for events ...
    >>> await subscriber.close()

Async iterator usage:
    >>> async for event in subscriber:
    ...     print(f"Received: {event}")
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Callable, Optional

from opencode_server_client.events.parser import EventParser
from opencode_server_client.events.types import (
    AnyEvent,
    MessagePartDeltaEvent,
    MessagePartUpdatedEvent,
    ServerConnectedEvent,
    ServerHeartbeatEvent,
    SessionDiffEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionUpdatedEvent,
)
from opencode_server_client.http_client.async_client import AsyncHttpClient

logger = logging.getLogger(__name__)


class AsyncEventSubscriber:
    """Subscribe to real-time events from /global/event SSE stream asynchronously.

    This class manages an asyncio task that reads SSE events from the
    server and invokes user callbacks. It supports:
    - Multiple simultaneous subscriptions with different callbacks
    - Session ID filtering (only process events for specific sessions)
    - Automatic reconnection with exponential backoff
    - Graceful shutdown
    - Async iterator pattern for event consumption

    Attributes:
        http_client: AsyncHttpClient instance for HTTP requests
        _listen_task: asyncio task reading SSE stream (or None)
        _cancel_event: asyncio event to signal task to stop
        _subscriptions: List of registered callbacks
        _lock: asyncio lock for thread-safe operations
    """

    INITIAL_RECONNECT_DELAY = 1.0
    MAX_RECONNECT_DELAY = 30.0
    RECONNECT_BASE = 2.0
    SHUTDOWN_TIMEOUT = 5.0

    def __init__(self, http_client: AsyncHttpClient):
        """Initialize the AsyncEventSubscriber.

        Args:
            http_client: AsyncHttpClient instance for making requests
        """
        self.http_client = http_client
        self._listen_task: Optional[asyncio.Task] = None
        self._cancel_event = asyncio.Event()
        self._subscriptions = []
        self._lock = asyncio.Lock()
        self._parser = EventParser()
        self._reconnect_attempt = 0
        self._event_queue: Optional[asyncio.Queue] = None

    async def subscribe(
        self,
        on_event: Optional[Callable[..., Any]] = None,
        on_idle: Optional[Callable[..., Any]] = None,
        on_error: Optional[Callable[..., Any]] = None,
        on_session_updated: Optional[Callable[..., Any]] = None,
        on_message_part_updated: Optional[Callable[..., Any]] = None,
        on_message_part_delta: Optional[Callable[..., Any]] = None,
        on_server_heartbeat: Optional[Callable[..., Any]] = None,
        on_session_diff: Optional[Callable[..., Any]] = None,
        on_server_connected: Optional[Callable[..., Any]] = None,
        session_id_filter: Optional[str] = None,
    ) -> None:
        """Register callbacks for events.

        Callbacks can be either sync or async functions. They will be invoked
        within the asyncio task context.

        Args:
            on_event: Callback for any event type
            on_idle: Callback for SessionIdleEvent only
            on_error: Callback for SessionErrorEvent only
            on_session_updated: Callback for SessionUpdatedEvent only
            on_message_part_updated: Callback for MessagePartUpdatedEvent only
            on_message_part_delta: Callback for MessagePartDeltaEvent only
            on_server_heartbeat: Callback for ServerHeartbeatEvent only
            on_session_diff: Callback for SessionDiffEvent only
            on_server_connected: Callback for ServerConnectedEvent only
            session_id_filter: Optional session_id to filter events

        Example:
            >>> async def on_idle(event):
            ...     print(f"Session {event.session_id} idle")
            >>> await subscriber.subscribe(
            ...     on_idle=on_idle,
            ...     session_id_filter="abc123"
            ... )
        """
        async with self._lock:
            self._subscriptions.append(
                {
                    "on_event": on_event,
                    "on_idle": on_idle,
                    "on_error": on_error,
                    "on_session_updated": on_session_updated,
                    "on_message_part_updated": on_message_part_updated,
                    "on_message_part_delta": on_message_part_delta,
                    "on_server_heartbeat": on_server_heartbeat,
                    "on_session_diff": on_session_diff,
                    "on_server_connected": on_server_connected,
                    "session_id_filter": session_id_filter,
                }
            )

            if self._listen_task is None or self._listen_task.done():
                self._cancel_event.clear()
                self._reconnect_attempt = 0
                self._event_queue = asyncio.Queue()
                self._listen_task = asyncio.create_task(self._read_sse_stream())
                logger.debug("Started SSE stream task")

    async def unsubscribe(self) -> None:
        """Remove all subscriptions and stop the asyncio task."""
        async with self._lock:
            self._subscriptions.clear()
            self._cancel_event.set()

    async def close(self, timeout: float = SHUTDOWN_TIMEOUT) -> None:
        """Gracefully shutdown the asyncio task.

        Args:
            timeout: Maximum time to wait for task to stop (seconds)

        Example:
            >>> await subscriber.close(timeout=5.0)
        """
        logger.debug("Closing AsyncEventSubscriber")
        self._cancel_event.set()

        if self._listen_task and not self._listen_task.done():
            try:
                await asyncio.wait_for(self._listen_task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    f"SSE stream task did not stop within {timeout}s timeout"
                )
                self._listen_task.cancel()
                try:
                    await self._listen_task
                except asyncio.CancelledError:
                    pass

    async def _read_sse_stream(self) -> None:
        """Asyncio task: Read SSE stream and dispatch events.

        This method runs in an asyncio task and:
        1. Connects to /global/event endpoint using http_client.stream()
        2. Reads SSE events using proper SSE parsing
        3. Parses event data using EventParser
        4. Invokes matching callbacks
        5. Handles reconnection on errors
        """
        while not self._cancel_event.is_set():
            try:
                self._reconnect_attempt += 1
                logger.debug(
                    f"Connecting to SSE stream (attempt {self._reconnect_attempt})"
                )

                async with self.http_client.stream("GET", "/global/event") as response:
                    response.raise_for_status()
                    self._reconnect_attempt = 0

                    event_data = {}
                    async for line in response.aiter_lines():
                        if self._cancel_event.is_set():
                            break

                        line = line.strip()
                        if not line:
                            if event_data.get("data"):
                                try:
                                    event = self._parser.parse(
                                        event_data["data"].encode("utf-8")
                                    )
                                    if event:
                                        self._dispatch_event(event)
                                        if self._event_queue:
                                            await self._event_queue.put(event)
                                except Exception as e:
                                    logger.error(f"Error parsing SSE event: {e}")
                            event_data = {}
                            continue

                        if ":" in line:
                            field, value = line.split(":", 1)
                            field = field.strip()
                            value = value.lstrip()

                            if field == "data":
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

                logger.debug("SSE stream ended normally")

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._cancel_event.is_set():
                    break

                logger.warning(f"SSE stream error: {e}")

                delay = min(
                    self.INITIAL_RECONNECT_DELAY
                    * (self.RECONNECT_BASE ** (self._reconnect_attempt - 1)),
                    self.MAX_RECONNECT_DELAY,
                )

                logger.debug(f"Reconnecting in {delay}s...")

                try:
                    await asyncio.wait_for(self._cancel_event.wait(), timeout=delay)
                except asyncio.TimeoutError:
                    continue
                else:
                    break

    def _dispatch_event(self, event: AnyEvent) -> None:
        """Dispatch event to matching callbacks.

        Args:
            event: Parsed event object to dispatch
        """
        for subscription in self._subscriptions:
            if subscription.get("session_id_filter"):
                if not hasattr(event, "session_id"):
                    continue
                if event.session_id != subscription["session_id_filter"]:
                    continue

            try:
                if subscription.get("on_event"):
                    self._invoke_callback(subscription["on_event"], event)

                if isinstance(event, SessionIdleEvent) and subscription.get("on_idle"):
                    self._invoke_callback(subscription["on_idle"], event)
                elif isinstance(event, SessionErrorEvent) and subscription.get(
                    "on_error"
                ):
                    self._invoke_callback(subscription["on_error"], event)
                elif isinstance(event, SessionUpdatedEvent) and subscription.get(
                    "on_session_updated"
                ):
                    self._invoke_callback(subscription["on_session_updated"], event)
                elif isinstance(event, MessagePartUpdatedEvent) and subscription.get(
                    "on_message_part_updated"
                ):
                    self._invoke_callback(
                        subscription["on_message_part_updated"], event
                    )
                elif isinstance(event, MessagePartDeltaEvent) and subscription.get(
                    "on_message_part_delta"
                ):
                    self._invoke_callback(subscription["on_message_part_delta"], event)
                elif isinstance(event, ServerHeartbeatEvent) and subscription.get(
                    "on_server_heartbeat"
                ):
                    self._invoke_callback(subscription["on_server_heartbeat"], event)
                elif isinstance(event, SessionDiffEvent) and subscription.get(
                    "on_session_diff"
                ):
                    self._invoke_callback(subscription["on_session_diff"], event)
                elif isinstance(event, ServerConnectedEvent) and subscription.get(
                    "on_server_connected"
                ):
                    self._invoke_callback(subscription["on_server_connected"], event)

            except Exception as e:
                logger.error(f"Error in event callback: {e}", exc_info=True)

    def _invoke_callback(self, callback: Callable[..., Any], event: AnyEvent) -> None:
        """Invoke a callback, handling both sync and async functions.

        Args:
            callback: The callback function to invoke
            event: The event to pass to the callback
        """

        if asyncio.iscoroutinefunction(callback):
            asyncio.create_task(callback(event))
        else:
            callback(event)

    async def __aiter__(self) -> AsyncGenerator[AnyEvent, None]:
        """Async iterator for consuming events.

        Yields:
            Events from the SSE stream

        Example:
            >>> async for event in subscriber:
            ...     print(f"Received: {event}")
        """
        if self._event_queue is None:
            self._event_queue = asyncio.Queue()

        if self._listen_task is None or self._listen_task.done():
            self._cancel_event.clear()
            self._reconnect_attempt = 0
            self._listen_task = asyncio.create_task(self._read_sse_stream())

        while not self._cancel_event.is_set():
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                continue

    async def __aenter__(self) -> "AsyncEventSubscriber":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
        return False
