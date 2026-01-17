"""Tests for GameVisualizerCallbackHandler."""

import asyncio
import pytest
from uuid import uuid4

from pixelgraph.callback import GameVisualizerCallbackHandler, GameEventType


@pytest.fixture
def event_queue():
    """Create a fresh event queue for each test."""
    return asyncio.Queue()


@pytest.fixture
def handler(event_queue):
    """Create a handler with the event queue."""
    return GameVisualizerCallbackHandler(event_queue, default_agent="test_agent")


class TestGameVisualizerCallbackHandler:
    """Tests for the callback handler."""

    def test_handler_initializes(self, handler):
        """Handler should initialize with correct defaults."""
        assert handler.current_active_agent == "test_agent"
        assert handler.queue is not None

    def test_emit_event_sync_creates_correct_structure(self, handler, event_queue):
        """Events should have the correct structure."""
        handler._emit_event_sync(
            GameEventType.AGENT_SPEAK,
            "wizard",
            {"content": "Hello!"}
        )

        # Check event was queued
        event = event_queue.get_nowait()

        assert "event_id" in event
        assert "timestamp" in event
        assert event["type"] == GameEventType.AGENT_SPEAK
        assert event["agent_id"] == "wizard"
        assert event["data"]["content"] == "Hello!"

    def test_on_chat_model_start_emits_think_event(self, handler, event_queue):
        """on_chat_model_start should emit AGENT_THINK_START event."""
        handler.on_chat_model_start(
            serialized={},
            messages=[],
            run_id=uuid4(),
            metadata={"agent_name": "wizard"}
        )

        event = event_queue.get_nowait()
        assert event["type"] == GameEventType.AGENT_THINK_START
        assert event["agent_id"] == "wizard"

    def test_on_tool_start_emits_tool_event(self, handler, event_queue):
        """on_tool_start should emit TOOL_START event with tool info."""
        handler.on_tool_start(
            serialized={"name": "web_search"},
            input_str="search query",
            run_id=uuid4()
        )

        event = event_queue.get_nowait()
        assert event["type"] == GameEventType.TOOL_START
        assert event["data"]["tool_name"] == "web_search"

    def test_agent_name_updates_from_metadata(self, handler, event_queue):
        """Current agent should update when specified in metadata."""
        handler.on_chat_model_start(
            serialized={},
            messages=[],
            run_id=uuid4(),
            metadata={"agent_name": "new_wizard"}
        )

        assert handler.current_active_agent == "new_wizard"

    def test_tool_end_truncates_long_output(self, handler, event_queue):
        """Tool end should truncate long outputs."""
        long_output = "x" * 100
        handler.on_tool_end(output=long_output, run_id=uuid4())

        event = event_queue.get_nowait()
        assert len(event["data"]["result_preview"]) < 100
        assert "..." in event["data"]["result_preview"]
