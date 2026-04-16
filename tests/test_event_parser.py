"""Tests for EventParser - converting raw SSE to typed events."""

from datetime import datetime
from unittest import TestCase

from opencode_server_client.events.parser import EventParser
from opencode_server_client.events.types import (
    MessagePartDeltaEvent,
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    ServerConnectedEvent,
    ServerHeartbeatEvent,
    SessionDiffEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionStatusEvent,
    SessionUpdatedEvent,
)


class TestEventParser(TestCase):
    """Test EventParser.parse() for all event types."""

    def setUp(self):
        self.parser = EventParser()

    def test_parse_session_status_event(self):
        """Test parsing SessionStatusEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "session.status", "properties": {"sessionID": "abc123", "status": "busy", "timestamp": "2024-04-15T10:00:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionStatusEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.status, "busy")

    def test_parse_session_idle_event(self):
        """Test parsing SessionIdleEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "session.idle", "properties": {"sessionID": "xyz789", "timestamp": "2024-04-15T10:05:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionIdleEvent)
        self.assertEqual(event.session_id, "xyz789")

    def test_parse_message_updated_event(self):
        """Test parsing MessageUpdatedEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "message.updated", "properties": {"sessionID": "abc123", "info": {"id": "msg1"}, "timestamp": "2024-04-15T10:01:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessageUpdatedEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.message_id, "msg1")

    def test_parse_message_part_updated_event(self):
        """Test parsing MessagePartUpdatedEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "message.part.updated", "properties": {"sessionID": "abc123", "messageID": "msg2", "part": {"id": "part0"}, "timestamp": "2024-04-15T10:02:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartUpdatedEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.message_id, "msg2")

    def test_parse_session_error_event(self):
        """Test parsing SessionErrorEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "session.error", "properties": {"sessionID": "abc123", "error_message": "Timeout", "error_code": "E001", "timestamp": "2024-04-15T10:03:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionErrorEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.error_message, "Timeout")
        self.assertEqual(event.error_code, "E001")

    def test_parse_unknown_event_type(self):
        """Test unknown event type returns None with warning."""
        sse_data = b'{"directory": null, "payload": {"type": "unknown.type", "properties": {"sessionID": "abc123"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsNone(event)

    def test_parse_invalid_json_raises_error(self):
        """Test invalid JSON in event data raises ValueError."""
        sse_data = b"{invalid json}"

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_missing_required_fields_raises_error(self):
        """Test missing required fields raises ValueError."""
        sse_data = b'{"directory": null, "payload": {"type": "session.idle", "properties": {"timestamp": "2024-04-15T10:00:00Z"}}}'  # missing sessionID

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_event_timestamp_formatting(self):
        """Test event timestamp parsing and formatting."""
        sse_data = b'{"directory": null, "payload": {"type": "session.idle", "properties": {"sessionID": "abc123", "timestamp": "2024-04-15T10:00:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event.timestamp, datetime)
        # Should be parseable
        self.assertIsNotNone(event.timestamp.isoformat())

    def test_parse_empty_data(self):
        """Test empty SSE data returns None."""
        event = self.parser.parse(b"")
        self.assertIsNone(event)

    def test_parse_whitespace_only(self):
        """Test whitespace-only SSE data returns None."""
        event = self.parser.parse(b"   \n  \n")
        self.assertIsNone(event)

    def test_parse_message_part_index_as_int(self):
        """Test MessagePartUpdatedEvent with part object."""
        sse_data = b'{"directory": null, "payload": {"type": "message.part.updated", "properties": {"sessionID": "abc123", "messageID": "msg2", "part": {"id": "part5"}, "timestamp": "2024-04-15T10:02:00Z"}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartUpdatedEvent)
        self.assertEqual(event.part_id, "part5")

    def test_parse_session_updated_event(self):
        """Test parsing SessionUpdatedEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "session.updated", "properties": {"sessionID": "abc123", "info": {"status": "busy", "user": "john"}, "time": 1713177600000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionUpdatedEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.info, {"status": "busy", "user": "john"})
        self.assertIsInstance(event.timestamp, datetime)

    def test_parse_session_updated_event_with_nested_info(self):
        """Test parsing SessionUpdatedEvent with nested info structure."""
        sse_data = b'{"directory": null, "payload": {"type": "session.updated", "properties": {"sessionID": "xyz789", "info": {"model": "gpt-4", "tokens": 1500, "metadata": {"nested": "value"}}, "time": 1713177605000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionUpdatedEvent)
        self.assertEqual(event.session_id, "xyz789")
        self.assertEqual(event.info["model"], "gpt-4")
        self.assertEqual(event.info["tokens"], 1500)
        self.assertEqual(event.info["metadata"]["nested"], "value")

    def test_parse_message_part_updated_event_with_part_object(self):
        """Test parsing new MessagePartUpdatedEvent with part object (not part_index)."""
        sse_data = b'{"directory": null, "payload": {"type": "message.part.updated", "properties": {"sessionID": "abc123", "messageID": "msg1", "part": {"id": "part1", "type": "text", "text": "Hello", "tokens": 2}, "time": 1713177601000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartUpdatedEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.message_id, "msg1")
        self.assertEqual(
            event.part, {"id": "part1", "type": "text", "text": "Hello", "tokens": 2}
        )
        self.assertEqual(event.part_id, "part1")
        self.assertIsInstance(event.timestamp, datetime)

    def test_parse_message_part_delta_event(self):
        """Test parsing MessagePartDeltaEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "message.part.delta", "properties": {"sessionID": "abc123", "messageID": "msg1", "partID": "part1", "field": "text", "delta": " world", "timestamp": 1713177602000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartDeltaEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.message_id, "msg1")
        self.assertEqual(event.part_id, "part1")
        self.assertEqual(event.field, "text")
        self.assertEqual(event.delta, " world")
        self.assertIsInstance(event.timestamp, datetime)

    def test_parse_message_part_delta_event_with_various_deltas(self):
        """Test parsing MessagePartDeltaEvent with different delta content."""
        # Test with empty delta
        sse_data = b'{"directory": null, "payload": {"type": "message.part.delta", "properties": {"sessionID": "abc123", "messageID": "msg1", "partID": "part1", "field": "text", "delta": "", "timestamp": 1713177602000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartDeltaEvent)
        self.assertEqual(event.delta, "")

        # Test with multi-line delta
        sse_data = b'{"directory": null, "payload": {"type": "message.part.delta", "properties": {"sessionID": "abc123", "messageID": "msg1", "partID": "part1", "field": "text", "delta": "line1\\nline2", "timestamp": 1713177602000}}}'
        event = self.parser.parse(sse_data)

        self.assertEqual(event.delta, "line1\nline2")

    def test_parse_session_updated_event_missing_session_id(self):
        """Test SessionUpdatedEvent with missing sessionID raises error."""
        sse_data = b'{"directory": null, "payload": {"type": "session.updated", "properties": {"info": {"status": "busy"}, "time": 1713177600000}}}'

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_message_part_updated_event_missing_message_id(self):
        """Test MessagePartUpdatedEvent with missing messageID raises error."""
        sse_data = b'{"directory": null, "payload": {"type": "message.part.updated", "properties": {"sessionID": "abc123", "part": {"id": "part1"}, "time": 1713177601000}}}'

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_message_part_delta_event_missing_delta(self):
        """Test MessagePartDeltaEvent with missing delta raises error."""
        sse_data = b'{"directory": null, "payload": {"type": "message.part.delta", "properties": {"sessionID": "abc123", "messageID": "msg1", "partID": "part1", "field": "text", "timestamp": 1713177602000}}}'

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_message_part_updated_event_missing_message_id(self):
        """Test MessagePartUpdatedEvent with missing messageID raises error."""
        sse_data = b'event: message.part.updated\ndata: {"sessionID": "abc123", "part": {"id": "part1"}, "time": 1713177601000}'

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_message_part_delta_event_missing_delta(self):
        """Test MessagePartDeltaEvent with missing delta raises error."""
        sse_data = b'event: message.part.delta\ndata: {"sessionID": "abc123", "messageID": "msg1", "partID": "part1", "field": "text", "timestamp": 1713177602000}'

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_server_heartbeat_event(self):
        """Test parsing ServerHeartbeatEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "server.heartbeat", "properties": {"timestamp": 1713177603000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, ServerHeartbeatEvent)
        self.assertIsInstance(event.timestamp, datetime)

    def test_parse_server_heartbeat_event_with_empty_properties(self):
        """Test parsing ServerHeartbeatEvent with empty properties."""
        sse_data = b'{"directory": null, "payload": {"type": "server.heartbeat", "properties": {}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, ServerHeartbeatEvent)

    def test_parse_session_diff_event(self):
        """Test parsing SessionDiffEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "session.diff", "properties": {"sessionID": "abc123", "diff": [{"op": "add", "path": "/status", "value": "busy"}], "timestamp": 1713177604000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionDiffEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(len(event.diff), 1)
        self.assertEqual(event.diff[0]["op"], "add")

    def test_parse_session_diff_event_with_empty_diff(self):
        """Test parsing SessionDiffEvent with empty diff list."""
        sse_data = b'{"directory": null, "payload": {"type": "session.diff", "properties": {"sessionID": "xyz789", "diff": [], "timestamp": 1713177604000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionDiffEvent)
        self.assertEqual(event.session_id, "xyz789")
        self.assertEqual(event.diff, [])

    def test_parse_session_diff_event_missing_session_id(self):
        """Test SessionDiffEvent with missing sessionID raises error."""
        sse_data = b'{"directory": null, "payload": {"type": "session.diff", "properties": {"diff": [], "timestamp": 1713177604000}}}'

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_session_error_event_with_nested_error_object(self):
        """Test parsing SessionErrorEvent with nested error object (new format)."""
        sse_data = b'{"directory": null, "payload": {"type": "session.error", "properties": {"sessionID": "abc123", "error": {"name": "TimeoutError", "data": {"message": "Request timed out"}}, "timestamp": 1713177605000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionErrorEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.error_message, "Request timed out")
        self.assertEqual(event.error_code, "TimeoutError")
        self.assertIsInstance(event.timestamp, datetime)

    def test_parse_server_connected_event(self):
        """Test parsing ServerConnectedEvent from raw SSE."""
        sse_data = b'{"directory": null, "payload": {"type": "server.connected", "properties": {"timestamp": 1713177606000}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, ServerConnectedEvent)
        self.assertIsInstance(event.timestamp, datetime)

    def test_parse_server_connected_event_with_empty_properties(self):
        """Test parsing ServerConnectedEvent with empty properties."""
        sse_data = b'{"directory": null, "payload": {"type": "server.connected", "properties": {}}}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, ServerConnectedEvent)
