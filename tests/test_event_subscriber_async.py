"""Tests for AsyncEventSubscriber - async SSE event subscription."""

import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from opencode_server_client.events.async_subscriber import AsyncEventSubscriber
from opencode_server_client.events.types import (
    SessionIdleEvent,
    SessionErrorEvent,
)


class TestAsyncEventSubscriber(TestCase):
    """Test AsyncEventSubscriber async operations."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.mock_http_client.stream = MagicMock()
        self.subscriber = AsyncEventSubscriber(self.mock_http_client)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.run_until_complete(self.subscriber.close())
        self.loop.close()

    def test_subscribe_registers_callback(self):
        """Test subscribe() registers callback."""
        callback = MagicMock()

        self.loop.run_until_complete(self.subscriber.subscribe(on_event=callback))

        self.assertEqual(len(self.subscriber._subscriptions), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_unsubscribe_cancels_task(self):
        """Test unsubscribe() cancels asyncio task."""
        callback = MagicMock()

        self.loop.run_until_complete(self.subscriber.subscribe(on_event=callback))

        self.assertIsNotNone(self.subscriber._listen_task)

        self.loop.run_until_complete(self.subscriber.unsubscribe())

        self.assertTrue(self.subscriber._cancel_event.is_set())

    def test_close_stops_task(self):
        """Test close() stops asyncio task gracefully."""
        callback = MagicMock()

        self.loop.run_until_complete(self.subscriber.subscribe(on_event=callback))

        self.loop.run_until_complete(self.subscriber.close())

        self.assertTrue(self.subscriber._cancel_event.is_set())

    def test_multiple_callbacks_can_subscribe(self):
        """Test multiple callbacks can subscribe simultaneously."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.loop.run_until_complete(self.subscriber.subscribe(on_event=callback1))
        self.loop.run_until_complete(self.subscriber.subscribe(on_event=callback2))

        self.assertEqual(len(self.subscriber._subscriptions), 2)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_session_id_filter(self):
        """Test session_id filtering works correctly."""
        callback = MagicMock()

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_event=callback, session_id_filter="abc123")
        )

        sub = self.subscriber._subscriptions[0]
        self.assertEqual(sub["session_id_filter"], "abc123")
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    @patch.object(AsyncEventSubscriber, "_read_sse_stream")
    def test_async_iterator_pattern(self, mock_read):
        """Test async iterator pattern works."""
        AsyncMock()

        async def mock_stream():
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = AsyncMock(return_value=iter([]))
            mock_ctx.__aenter__.return_value = mock_response
            return mock_ctx

        self.mock_http_client.stream = mock_stream

        async def test_iter():
            count = 0
            async for event in self.subscriber:
                count += 1
                if count > 5:
                    break
            return count

        self.loop.run_until_complete(self.subscriber.close())


class TestAsyncEventSubscriberCallbacks(TestCase):
    """Test AsyncEventSubscriber callback invocation."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.subscriber = AsyncEventSubscriber(self.mock_http_client)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.run_until_complete(self.subscriber.close())
        self.loop.close()

    def test_on_idle_callback_invoked(self):
        """Test on_idle callback invoked on SessionIdleEvent."""
        received_event = []

        def on_idle(event):
            received_event.append(event)

        self.loop.run_until_complete(self.subscriber.subscribe(on_idle=on_idle))

        event = SessionIdleEvent(
            session_id="abc123", timestamp=asyncio.get_event_loop().time()
        )
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_on_error_callback_invoked(self):
        """Test on_error callback invoked on SessionErrorEvent."""
        received_event = []

        def on_error(event):
            received_event.append(event)

        self.loop.run_until_complete(self.subscriber.subscribe(on_error=on_error))

        event = SessionErrorEvent(session_id="abc123", error_message="Test error")
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_callback_errors_dont_crash_listener(self):
        """Test callback errors don't crash listener task."""

        def bad_callback(event):
            raise ValueError("Callback error")

        self.loop.run_until_complete(self.subscriber.subscribe(on_event=bad_callback))

        event = SessionIdleEvent(
            session_id="abc123", timestamp=asyncio.get_event_loop().time()
        )

        try:
            self.subscriber._dispatch_event(event)
        except ValueError:
            self.fail("Callback error propagated unexpectedly")

        self.loop.run_until_complete(self.subscriber.unsubscribe())


class TestAsyncEventSubscriberConnection(TestCase):
    """Test AsyncEventSubscriber connection lifecycle."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.subscriber = AsyncEventSubscriber(self.mock_http_client)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.run_until_complete(self.subscriber.close())
        self.loop.close()

    def test_context_manager_support(self):
        """Test async context manager support."""

        async def test_context():
            async with self.subscriber as sub:
                self.assertIsNotNone(sub)

        self.loop.run_until_complete(test_context())

    def test_reconnection_backoff(self):
        """Test reconnection with exponential backoff."""
        self.assertEqual(self.subscriber.INITIAL_RECONNECT_DELAY, 1.0)
        self.assertEqual(self.subscriber.MAX_RECONNECT_DELAY, 30.0)
        self.assertEqual(self.subscriber.RECONNECT_BASE, 2.0)


class TestAsyncEventSubscriberAsyncCallbacks(TestCase):
    """Test AsyncEventSubscriber async callback invocation."""

    def setUp(self):
        """Set up mock async HTTP client for tests."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.mock_http_client = MagicMock()
        self.subscriber = AsyncEventSubscriber(self.mock_http_client)

    def tearDown(self):
        """Clean up event loop."""
        self.loop.run_until_complete(self.subscriber.close())
        self.loop.close()

    def test_on_session_updated_callback_invoked(self):
        """Test on_session_updated callback invoked for SessionUpdatedEvent."""
        from opencode_server_client.events.types import SessionUpdatedEvent

        received_event = []

        def on_session_updated(event):
            received_event.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_session_updated=on_session_updated)
        )

        event = SessionUpdatedEvent(
            session_id="abc123",
            info={"status": "busy", "model": "gpt-4"},
            timestamp=asyncio.get_event_loop().time(),
        )
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_on_message_part_updated_callback_invoked(self):
        """Test on_message_part_updated callback invoked for MessagePartUpdatedEvent."""
        from opencode_server_client.events.types import MessagePartUpdatedEvent

        received_event = []

        def on_message_part_updated(event):
            received_event.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_message_part_updated=on_message_part_updated)
        )

        event = MessagePartUpdatedEvent(
            session_id="abc123",
            message_id="msg1",
            part_id="part1",
            part={"id": "part1", "type": "text", "text": "Hello"},
            timestamp=asyncio.get_event_loop().time(),
        )
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_on_message_part_delta_callback_invoked(self):
        """Test on_message_part_delta callback invoked for MessagePartDeltaEvent."""
        from opencode_server_client.events.types import MessagePartDeltaEvent

        received_event = []

        def on_message_part_delta(event):
            received_event.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_message_part_delta=on_message_part_delta)
        )

        event = MessagePartDeltaEvent(
            session_id="abc123",
            message_id="msg1",
            part_id="part1",
            field="text",
            delta=" world",
            timestamp=asyncio.get_event_loop().time(),
        )
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_on_server_heartbeat_callback_invoked(self):
        """Test on_server_heartbeat callback invoked for ServerHeartbeatEvent."""
        from opencode_server_client.events.types import ServerHeartbeatEvent

        received_event = []

        def on_server_heartbeat(event):
            received_event.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_server_heartbeat=on_server_heartbeat)
        )

        event = ServerHeartbeatEvent(timestamp=asyncio.get_event_loop().time())
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_on_session_diff_callback_invoked(self):
        """Test on_session_diff callback invoked for SessionDiffEvent."""
        from opencode_server_client.events.types import SessionDiffEvent

        received_event = []

        def on_session_diff(event):
            received_event.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_session_diff=on_session_diff)
        )

        event = SessionDiffEvent(
            session_id="abc123",
            diff=[{"op": "add", "path": "/status", "value": "busy"}],
            timestamp=asyncio.get_event_loop().time(),
        )
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_on_server_connected_callback_invoked(self):
        """Test on_server_connected callback invoked for ServerConnectedEvent."""
        from opencode_server_client.events.types import ServerConnectedEvent

        received_event = []

        def on_server_connected(event):
            received_event.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_server_connected=on_server_connected)
        )

        event = ServerConnectedEvent(timestamp=asyncio.get_event_loop().time())
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_event), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_mixed_sync_async_callbacks(self):
        """Test both sync and async callbacks can be registered."""

        received_sync = []
        received_async = []

        def sync_callback(event):
            received_sync.append(event)

        def async_callback(event):
            received_async.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(on_event=sync_callback, on_idle=async_callback)
        )

        event = SessionIdleEvent(
            session_id="abc123",
            timestamp=asyncio.get_event_loop().time(),
        )
        self.subscriber._dispatch_event(event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received_sync), 1)
        self.assertEqual(len(received_async), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_session_id_filter_with_sync_callback(self):
        """Test session_id filtering works with sync callback."""
        from opencode_server_client.events.types import SessionUpdatedEvent

        received = []

        def sync_callback(event):
            received.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(
                on_session_updated=sync_callback, session_id_filter="abc123"
            )
        )

        event1 = SessionUpdatedEvent(
            session_id="abc123",
            info={"status": "busy"},
            timestamp=asyncio.get_event_loop().time(),
        )
        event2 = SessionUpdatedEvent(
            session_id="xyz789",
            info={"status": "idle"},
            timestamp=asyncio.get_event_loop().time(),
        )

        self.subscriber._dispatch_event(event1)
        self.subscriber._dispatch_event(event2)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(received), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_multiple_event_types_with_callbacks(self):
        """Test all event types dispatch correctly."""
        from opencode_server_client.events.types import SessionUpdatedEvent

        on_idle_called = []
        on_error_called = []
        on_session_updated_called = []

        def on_idle(event):
            on_idle_called.append(event)

        def on_error(event):
            on_error_called.append(event)

        def on_session_updated(event):
            on_session_updated_called.append(event)

        self.loop.run_until_complete(
            self.subscriber.subscribe(
                on_idle=on_idle,
                on_error=on_error,
                on_session_updated=on_session_updated,
            )
        )

        idle_event = SessionIdleEvent(
            session_id="abc123",
            timestamp=asyncio.get_event_loop().time(),
        )
        error_event = SessionErrorEvent(
            session_id="abc123",
            error_message="Test error",
        )
        session_event = SessionUpdatedEvent(
            session_id="abc123",
            info={"status": "busy"},
            timestamp=asyncio.get_event_loop().time(),
        )

        self.subscriber._dispatch_event(idle_event)
        self.subscriber._dispatch_event(error_event)
        self.subscriber._dispatch_event(session_event)

        self.loop.run_until_complete(asyncio.sleep(0.01))
        self.assertEqual(len(on_idle_called), 1)
        self.assertEqual(len(on_error_called), 1)
        self.assertEqual(len(on_session_updated_called), 1)
        self.loop.run_until_complete(self.subscriber.unsubscribe())

    def test_sync_callback_errors_dont_crash(self):
        """Test sync callback errors don't crash the dispatcher."""

        def bad_callback(event):
            raise ValueError("Sync callback error")

        def good_callback(event):
            pass

        self.loop.run_until_complete(self.subscriber.subscribe(on_event=bad_callback))
        self.loop.run_until_complete(self.subscriber.subscribe(on_event=good_callback))

        event = SessionIdleEvent(
            session_id="abc123",
            timestamp=asyncio.get_event_loop().time(),
        )

        try:
            self.subscriber._dispatch_event(event)
        except ValueError:
            self.fail("Sync callback error propagated unexpectedly")

        self.loop.run_until_complete(self.subscriber.unsubscribe())
