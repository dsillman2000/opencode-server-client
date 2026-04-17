"""Tests for EventSubscriber - sync SSE event subscription with background thread."""

import time
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from opencode_server_client.events.sync_subscriber import EventSubscriber
from opencode_server_client.events.types import (
    MessagePartDeltaEvent,
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    ServerConnectedEvent,
    ServerHeartbeatEvent,
    SessionDiffEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionUpdatedEvent,
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

        now = datetime.now()
        event = MessageUpdatedEvent(
            session_id="abc123",
            message_id="msg1",
            cost=0.42,
            tokens={"input": 12, "output": 34},
            created_timestamp=now,
            completed_timestamp=now,
            timestamp=now,
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

    def test_on_session_updated_callback_invoked(self):
        """Test on_session_updated callback invoked for SessionUpdatedEvent."""
        session_updated_callback = MagicMock()
        self.subscriber.subscribe(on_session_updated=session_updated_callback)

        event = SessionUpdatedEvent(
            session_id="abc123",
            info={"status": "busy", "model": "gpt-4"},
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        session_updated_callback.assert_called_once_with(event)

    def test_on_message_part_updated_callback_invoked(self):
        """Test on_message_part_updated callback invoked for MessagePartUpdatedEvent."""
        part_updated_callback = MagicMock()
        self.subscriber.subscribe(on_message_part_updated=part_updated_callback)

        event = MessagePartUpdatedEvent(
            session_id="abc123",
            message_id="msg1",
            part_id="part1",
            part={"id": "part1", "type": "text", "text": "Hello"},
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        part_updated_callback.assert_called_once_with(event)

    def test_on_message_part_delta_callback_invoked(self):
        """Test on_message_part_delta callback invoked for MessagePartDeltaEvent."""
        part_delta_callback = MagicMock()
        self.subscriber.subscribe(on_message_part_delta=part_delta_callback)

        event = MessagePartDeltaEvent(
            session_id="abc123",
            message_id="msg1",
            part_id="part1",
            field="text",
            delta=" world",
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        part_delta_callback.assert_called_once_with(event)

    def test_all_new_callbacks_registered(self):
        """Test all three new callbacks can be registered together."""
        session_updated_callback = MagicMock()
        part_updated_callback = MagicMock()
        part_delta_callback = MagicMock()

        self.subscriber.subscribe(
            on_session_updated=session_updated_callback,
            on_message_part_updated=part_updated_callback,
            on_message_part_delta=part_delta_callback,
        )

        self.assertEqual(len(self.subscriber._subscriptions), 1)
        subscription = self.subscriber._subscriptions[0]
        self.assertEqual(subscription["on_session_updated"], session_updated_callback)
        self.assertEqual(subscription["on_message_part_updated"], part_updated_callback)
        self.assertEqual(subscription["on_message_part_delta"], part_delta_callback)

    def test_session_updated_with_filtering(self):
        """Test SessionUpdatedEvent with session_id filtering."""
        callback_filtered = MagicMock()
        callback_all = MagicMock()

        self.subscriber.subscribe(
            on_session_updated=callback_filtered,
            session_id_filter="abc123",
        )
        self.subscriber.subscribe(on_session_updated=callback_all)

        # Event for filtered session
        event1 = SessionUpdatedEvent(
            session_id="abc123",
            info={"status": "busy"},
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event1)

        # Event for different session
        event2 = SessionUpdatedEvent(
            session_id="xyz789",
            info={"status": "idle"},
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event2)

        # Filtered callback called once (only for matching session)
        self.assertEqual(callback_filtered.call_count, 1)
        # All callback called twice (for both events)
        self.assertEqual(callback_all.call_count, 2)

    def test_message_part_delta_with_filtering(self):
        """Test MessagePartDeltaEvent with session_id filtering."""
        callback_filtered = MagicMock()
        callback_all = MagicMock()

        self.subscriber.subscribe(
            on_message_part_delta=callback_filtered,
            session_id_filter="session1",
        )
        self.subscriber.subscribe(on_message_part_delta=callback_all)

        # Event for filtered session
        event1 = MessagePartDeltaEvent(
            session_id="session1",
            message_id="msg1",
            part_id="part1",
            field="text",
            delta="hello",
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event1)

        # Event for different session
        event2 = MessagePartDeltaEvent(
            session_id="session2",
            message_id="msg1",
            part_id="part1",
            field="text",
            delta=" world",
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event2)

        # Filtered callback called once (only for matching session)
        self.assertEqual(callback_filtered.call_count, 1)
        # All callback called twice (for both events)
        self.assertEqual(callback_all.call_count, 2)

    def test_mixed_callbacks_dispatch(self):
        """Test all event types dispatched with mixed callbacks."""
        on_event_callback = MagicMock()
        on_session_updated_callback = MagicMock()
        on_part_delta_callback = MagicMock()

        self.subscriber.subscribe(
            on_event=on_event_callback,
            on_session_updated=on_session_updated_callback,
            on_message_part_delta=on_part_delta_callback,
        )

        # Dispatch SessionUpdatedEvent
        session_event = SessionUpdatedEvent(
            session_id="abc123",
            info={"status": "busy"},
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(session_event)

        # Dispatch MessagePartDeltaEvent
        delta_event = MessagePartDeltaEvent(
            session_id="abc123",
            message_id="msg1",
            part_id="part1",
            field="text",
            delta="test",
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(delta_event)

        # on_event should be called for both
        self.assertEqual(on_event_callback.call_count, 2)
        # on_session_updated should be called once
        self.assertEqual(on_session_updated_callback.call_count, 1)
        # on_part_delta should be called once
        self.assertEqual(on_part_delta_callback.call_count, 1)

    def test_on_server_heartbeat_callback_invoked(self):
        """Test on_server_heartbeat callback invoked for ServerHeartbeatEvent."""
        heartbeat_callback = MagicMock()
        self.subscriber.subscribe(on_server_heartbeat=heartbeat_callback)

        event = ServerHeartbeatEvent(timestamp=datetime.now())

        self.subscriber._dispatch_event(event)

        heartbeat_callback.assert_called_once_with(event)

    def test_on_session_diff_callback_invoked(self):
        """Test on_session_diff callback invoked for SessionDiffEvent."""
        diff_callback = MagicMock()
        self.subscriber.subscribe(on_session_diff=diff_callback)

        event = SessionDiffEvent(
            session_id="abc123",
            diff=[{"op": "add", "path": "/status", "value": "busy"}],
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        diff_callback.assert_called_once_with(event)

    def test_on_session_diff_callback_invoked_with_empty_diff(self):
        """Test on_session_diff callback invoked with empty diff list."""
        diff_callback = MagicMock()
        self.subscriber.subscribe(on_session_diff=diff_callback)

        event = SessionDiffEvent(
            session_id="xyz789",
            diff=[],
            timestamp=datetime.now(),
        )

        self.subscriber._dispatch_event(event)

        diff_callback.assert_called_once_with(event)

    def test_session_diff_with_filtering(self):
        """Test SessionDiffEvent with session_id filtering."""
        callback_filtered = MagicMock()
        callback_all = MagicMock()

        self.subscriber.subscribe(
            on_session_diff=callback_filtered,
            session_id_filter="session1",
        )
        self.subscriber.subscribe(on_session_diff=callback_all)

        # Event for filtered session
        event1 = SessionDiffEvent(
            session_id="session1",
            diff=[{"op": "add", "path": "/x", "value": "y"}],
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event1)

        # Event for different session
        event2 = SessionDiffEvent(
            session_id="session2",
            diff=[{"op": "remove", "path": "/x"}],
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(event2)

        # Filtered callback called once (only for matching session)
        self.assertEqual(callback_filtered.call_count, 1)
        # All callback called twice (for both events)
        self.assertEqual(callback_all.call_count, 2)

    def test_heartbeat_event_without_session_id(self):
        """Test ServerHeartbeatEvent dispatch (doesn't have session_id)."""
        callback = MagicMock()
        self.subscriber.subscribe(on_event=callback)

        event = ServerHeartbeatEvent(timestamp=datetime.now())

        self.subscriber._dispatch_event(event)

        # Generic callback should still be called
        callback.assert_called_once_with(event)

    def test_all_new_callbacks_registered_together(self):
        """Test new callbacks can be registered with other callbacks."""
        heartbeat_callback = MagicMock()
        diff_callback = MagicMock()
        on_event_callback = MagicMock()

        self.subscriber.subscribe(
            on_event=on_event_callback,
            on_server_heartbeat=heartbeat_callback,
            on_session_diff=diff_callback,
        )

        self.assertEqual(len(self.subscriber._subscriptions), 1)
        subscription = self.subscriber._subscriptions[0]
        self.assertEqual(subscription["on_server_heartbeat"], heartbeat_callback)
        self.assertEqual(subscription["on_session_diff"], diff_callback)
        self.assertEqual(subscription["on_event"], on_event_callback)

    def test_mixed_new_and_old_callbacks_dispatch(self):
        """Test all event types dispatched with new and old callbacks."""
        on_heartbeat_callback = MagicMock()
        on_diff_callback = MagicMock()
        on_event_callback = MagicMock()
        on_idle_callback = MagicMock()

        self.subscriber.subscribe(
            on_event=on_event_callback,
            on_idle=on_idle_callback,
            on_server_heartbeat=on_heartbeat_callback,
            on_session_diff=on_diff_callback,
        )

        # Dispatch heartbeat event
        heartbeat_event = ServerHeartbeatEvent(timestamp=datetime.now())
        self.subscriber._dispatch_event(heartbeat_event)

        # Dispatch idle event
        idle_event = SessionIdleEvent(
            session_id="abc123",
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(idle_event)

        # Dispatch diff event
        diff_event = SessionDiffEvent(
            session_id="abc123",
            diff=[],
            timestamp=datetime.now(),
        )
        self.subscriber._dispatch_event(diff_event)

        # on_event should be called for all three
        self.assertEqual(on_event_callback.call_count, 3)
        # on_idle should be called once
        self.assertEqual(on_idle_callback.call_count, 1)
        # on_heartbeat should be called once
        self.assertEqual(on_heartbeat_callback.call_count, 1)
        # on_diff should be called once
        self.assertEqual(on_diff_callback.call_count, 1)

    def test_on_server_connected_callback_invoked(self):
        """Test on_server_connected callback invoked for ServerConnectedEvent."""
        connected_callback = MagicMock()
        self.subscriber.subscribe(on_server_connected=connected_callback)

        event = ServerConnectedEvent(timestamp=datetime.now())

        self.subscriber._dispatch_event(event)

        connected_callback.assert_called_once_with(event)

    def test_server_connected_without_session_id(self):
        """Test ServerConnectedEvent dispatch (doesn't have session_id)."""
        callback = MagicMock()
        self.subscriber.subscribe(on_event=callback)

        event = ServerConnectedEvent(timestamp=datetime.now())

        self.subscriber._dispatch_event(event)

        # Generic callback should still be called
        callback.assert_called_once_with(event)

    def test_all_server_events_callbacks_registered(self):
        """Test all server event callbacks can be registered together."""
        heartbeat_callback = MagicMock()
        connected_callback = MagicMock()
        on_event_callback = MagicMock()

        self.subscriber.subscribe(
            on_event=on_event_callback,
            on_server_heartbeat=heartbeat_callback,
            on_server_connected=connected_callback,
        )

        self.assertEqual(len(self.subscriber._subscriptions), 1)
        subscription = self.subscriber._subscriptions[0]
        self.assertEqual(subscription["on_server_heartbeat"], heartbeat_callback)
        self.assertEqual(subscription["on_server_connected"], connected_callback)
        self.assertEqual(subscription["on_event"], on_event_callback)

    def test_server_connected_and_heartbeat_dispatch(self):
        """Test ServerConnectedEvent and ServerHeartbeatEvent dispatched together."""
        on_connected_callback = MagicMock()
        on_heartbeat_callback = MagicMock()
        on_event_callback = MagicMock()

        self.subscriber.subscribe(
            on_event=on_event_callback,
            on_server_connected=on_connected_callback,
            on_server_heartbeat=on_heartbeat_callback,
        )

        # Dispatch connected event
        connected_event = ServerConnectedEvent(timestamp=datetime.now())
        self.subscriber._dispatch_event(connected_event)

        # Dispatch heartbeat event
        heartbeat_event = ServerHeartbeatEvent(timestamp=datetime.now())
        self.subscriber._dispatch_event(heartbeat_event)

        # on_event should be called for both
        self.assertEqual(on_event_callback.call_count, 2)
        # on_connected should be called once
        self.assertEqual(on_connected_callback.call_count, 1)
        # on_heartbeat should be called once
        self.assertEqual(on_heartbeat_callback.call_count, 1)
