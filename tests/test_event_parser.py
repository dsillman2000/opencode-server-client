"""Tests for EventParser - converting raw SSE to typed events."""

from datetime import datetime
from unittest import TestCase

from opencode_server_client.events.parser import EventParser
from opencode_server_client.events.types import (
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    SessionErrorEvent,
    SessionIdleEvent,
    SessionStatusEvent,
)


class TestEventParser(TestCase):
    """Test EventParser.parse() for all event types."""

    def setUp(self):
        self.parser = EventParser()

    def test_parse_session_status_event(self):
        """Test parsing SessionStatusEvent from raw SSE."""
        sse_data = b'event: session.status\ndata: {"session_id": "abc123", "status": "busy", "timestamp": "2024-04-15T10:00:00Z"}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionStatusEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.status, "busy")

    def test_parse_session_idle_event(self):
        """Test parsing SessionIdleEvent from raw SSE."""
        sse_data = b'event: session.idle\ndata: {"session_id": "xyz789", "timestamp": "2024-04-15T10:05:00Z"}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionIdleEvent)
        self.assertEqual(event.session_id, "xyz789")

    def test_parse_message_updated_event(self):
        """Test parsing MessageUpdatedEvent from raw SSE."""
        sse_data = b'event: message.updated\ndata: {"session_id": "abc123", "message_id": "msg1", "content": "Hello", "timestamp": "2024-04-15T10:01:00Z"}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessageUpdatedEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.message_id, "msg1")
        self.assertEqual(event.content, "Hello")

    def test_parse_message_part_updated_event(self):
        """Test parsing MessagePartUpdatedEvent from raw SSE."""
        sse_data = b'event: message.part_updated\ndata: {"session_id": "abc123", "message_id": "msg2", "part_index": 0, "content": "Part 1", "timestamp": "2024-04-15T10:02:00Z"}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartUpdatedEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.message_id, "msg2")
        self.assertEqual(event.part_index, 0)
        self.assertEqual(event.content, "Part 1")

    def test_parse_session_error_event(self):
        """Test parsing SessionErrorEvent from raw SSE."""
        sse_data = b'event: session.error\ndata: {"session_id": "abc123", "error_message": "Timeout", "error_code": "E001", "timestamp": "2024-04-15T10:03:00Z"}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, SessionErrorEvent)
        self.assertEqual(event.session_id, "abc123")
        self.assertEqual(event.error_message, "Timeout")
        self.assertEqual(event.error_code, "E001")

    def test_parse_unknown_event_type(self):
        """Test unknown event type returns None with warning."""
        sse_data = b'event: unknown.type\ndata: {"session_id": "abc123"}'
        event = self.parser.parse(sse_data)

        self.assertIsNone(event)

    def test_parse_invalid_json_raises_error(self):
        """Test invalid JSON in event data raises ValueError."""
        sse_data = b"event: session.idle\ndata: {invalid json}"

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_missing_required_fields_raises_error(self):
        """Test missing required fields raises ValueError."""
        sse_data = b'event: session.idle\ndata: {"timestamp": "2024-04-15T10:00:00Z"}'  # missing session_id

        with self.assertRaises(ValueError):
            self.parser.parse(sse_data)

    def test_parse_event_timestamp_formatting(self):
        """Test event timestamp parsing and formatting."""
        sse_data = b'event: session.idle\ndata: {"session_id": "abc123", "timestamp": "2024-04-15T10:00:00Z"}'
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
        """Test MessagePartUpdatedEvent part_index is converted to int."""
        sse_data = b'event: message.part_updated\ndata: {"session_id": "abc123", "message_id": "msg2", "part_index": "5", "content": "Part", "timestamp": "2024-04-15T10:02:00Z"}'
        event = self.parser.parse(sse_data)

        self.assertIsInstance(event, MessagePartUpdatedEvent)
        self.assertEqual(event.part_index, 5)
        self.assertIsInstance(event.part_index, int)
