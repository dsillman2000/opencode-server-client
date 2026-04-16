"""Tests for EventSubscriber - sync SSE event subscription with background thread."""

import time
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from opencode_server_client.events.sync_subscriber import EventSubscriber
from opencode_server_client.events.types import (
    MessageUpdatedEvent,
    SessionErrorEvent,
    SessionIdleEvent,
)


class TestEventSubscriber(TestCase):
    """Test EventSubscriber operations."""

    def setUp(self):
        """Set up mock HTTP client for tests."""
        self.mock_http_client = MagicMock()
        self.subscriber = EventSubscriber(self.mock_http_client)

    def tearDown(self):
        """Cleanup subscriber resources."""
        self.subscriber.close(timeout=1.0)

    def test_subscribe_registers_callbacks(self):
        """Test subscribe() registers callbacks."""
        callback = MagicMock()

        self.subscriber.subscribe(on_event=callback)

        self.assertEqual(len(self.subscriber._subscriptions), 1)
        self.assertEqual(self.subscriber._subscriptions[0]["on_event"], callback)

    def test_unsubscribe_clears_callbacks(self):
        """Test unsubscribe() clears callbacks and sets stop event."""
        callback = MagicMock()
        self.subscriber.subscribe(on_event=callback)

        self.subscriber.unsubscribe()

        self.assertEqual(len(self.subscriber._subscriptions), 0)
        self.assertTrue(self.subscriber._stop_event.is_set())

    def test_close_stops_background_thread(self):
        """Test close() stops background thread gracefully."""
        # Create subscriber with mock
        with patch.object(self.subscriber, "_read_sse_stream"):
            callback = MagicMock()
            self.subscriber.subscribe(on_event=callback)

            # Thread should be started
            self.assertIsNotNone(self.subscriber._stream_thread)

            self.subscriber.close(timeout=1.0)

            # Stop event should be set
            self.assertTrue(self.subscriber._stop_event.is_set())

    def test_subscribe_starts_background_thread(self):
        """Test background thread starts on first subscription."""
        with patch.object(self.subscriber, "_read_sse_stream"):
            callback = MagicMock()

            # Thread should not exist yet
            self.assertIsNone(self.subscriber._stream_thread)

            self.subscriber.subscribe(on_event=callback)

            # Thread should be created
            self.assertIsNotNone(self.subscriber._stream_thread)

    def test_callback_invoked_on_event(self):
        """Test callback is invoked when event is dispatched."""
        callback = MagicMock()
        self.subscriber.subscribe(on_event=callback)

        # Create a test event
        event = SessionIdleEvent(
            session_id="abc123",
            timestamp=datetime.now(),
        )

        # Manually dispatch (in real usage, background thread does this)
        self.subscriber._dispatch_event(event)

        # Callback should have been called
        callback.assert_called_once_with(event)

    def test_on_idle_callback_invoked(self):
        """Test on_idle callback invoked for SessionIdleEvent."""
        idle_callback = MagicMock()
        self.subscriber.subscribe(on_idle=idle_callback)

        event = SessionIdleEvent(
            session_id="abc123",
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        idle_callback.assert_called_once_with(event)

    def test_on_error_callback_invoked(self):
        """Test on_error callback invoked for SessionErrorEvent."""
        error_callback = MagicMock()
        self.subscriber.subscribe(on_error=error_callback)

        event = SessionErrorEvent(
            session_id="abc123",
            error_message="Timeout",
        )

        self.subscriber._dispatch_event(event)

        error_callback.assert_called_once_with(event)

    def test_multiple_callbacks_subscribe_simultaneously(self):
        """Test multiple callbacks can subscribe to same events."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.subscriber.subscribe(on_event=callback1)
        self.subscriber.subscribe(on_event=callback2)

        self.assertEqual(len(self.subscriber._subscriptions), 2)

        event = SessionIdleEvent(
            session_id="abc123",
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        # Both callbacks should be called
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_session_id_filtering(self):
        """Test session_id filtering: only matching events trigger callbacks."""
        callback_filtered = MagicMock()
        callback_all = MagicMock()

        self.subscriber.subscribe(
            on_event=callback_filtered,
            session_id_filter="abc123",
        )
        self.subscriber.subscribe(on_event=callback_all)

        # Event for filtered session
        event1 = SessionIdleEvent(
            session_id="abc123",
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event1)

        # Event for different session
        event2 = SessionIdleEvent(
            session_id="xyz789",
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event2)

        # Filtered callback called once (only for matching session)
        self.assertEqual(callback_filtered.call_count, 1)
        # All callback called twice (for both events)
        self.assertEqual(callback_all.call_count, 2)

    def test_callback_errors_dont_crash_thread(self):
        """Test callback errors don't crash background thread."""
        error_callback = MagicMock(side_effect=Exception("Callback error"))
        good_callback = MagicMock()

        self.subscriber.subscribe(on_event=error_callback)
        self.subscriber.subscribe(on_event=good_callback)

        event = SessionIdleEvent(
            session_id="abc123",
            timestamp=datetime.now(),
        )

        # This should not raise
        self.subscriber._dispatch_event(event)

        # Good callback should still be called
        good_callback.assert_called_once()

    def test_unsubscribe_specific_subscription(self):
        """Test that unsubscribe clears all subscriptions."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        self.subscriber.subscribe(on_event=callback1)
        self.subscriber.subscribe(on_event=callback2)

        self.assertEqual(len(self.subscriber._subscriptions), 2)

        self.subscriber.unsubscribe()

        self.assertEqual(len(self.subscriber._subscriptions), 0)

    def test_thread_safe_callback_invocation(self):
        """Test thread-safe callback invocation with lock."""
        results = []

        def callback(event):
            results.append(event.session_id)
            time.sleep(0.01)  # Simulate slow callback

        self.subscriber.subscribe(on_event=callback)

        # Dispatch multiple events in sequence
        for i in range(5):
            event = SessionIdleEvent(
                session_id=f"session_{i}",
                timestamp=datetime.now(),
            )
            self.subscriber._dispatch_event(event)

        # All callbacks should have been called
        self.assertEqual(len(results), 5)

    def test_message_updated_event_dispatch(self):
        """Test MessageUpdatedEvent dispatch with callback."""
        callback = MagicMock()
        self.subscriber.subscribe(on_event=callback)

        event = MessageUpdatedEvent(
            session_id="abc123",
            message_id="msg1",
            content="Hello",
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        callback.assert_called_once_with(event)

    def test_event_without_session_id_filtered(self):
        """Test events without session_id attribute don't match filters."""
        callback_filtered = MagicMock()

        self.subscriber.subscribe(
            on_event=callback_filtered,
            session_id_filter="abc123",
        )

        # Create a simple event-like object without session_id
        class SimpleEvent:
            pass

        event = SimpleEvent()

        self.subscriber._dispatch_event(event)

        # Should not be called (event doesn't match filter)
        callback_filtered.assert_not_called()
