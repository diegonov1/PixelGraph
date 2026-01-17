"""
GameVisualizerCallbackHandler - The bridge between LangGraph and the visualization.

This callback handler captures events from LangChain/LangGraph execution
and transforms them into game events for the 8-bit frontend.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult, ChatGeneration


class GameEventType:
    """Event types that the frontend (Phaser) understands."""

    AGENT_THINK_START = "AGENT_THINK_START"
    AGENT_SPEAK = "AGENT_SPEAK"
    TOOL_START = "TOOL_START"
    TOOL_END = "TOOL_END"
    AGENT_IDLE = "AGENT_IDLE"
    ERROR = "ERROR"


class GameVisualizerCallbackHandler(BaseCallbackHandler):
    """
    Captures LangGraph/LangChain events and sends them to an async queue
    for consumption by a WebSocket connection.

    This handler acts as a "spy" that observes the execution flow without
    interfering with it, transforming internal events into visual instructions.
    """

    def __init__(self, event_queue: asyncio.Queue, default_agent: str = "agent"):
        """
        Initialize the callback handler.

        Args:
            event_queue: Async queue where events will be pushed
            default_agent: Default agent name when none is specified in metadata
        """
        super().__init__()
        self.queue = event_queue
        self.current_active_agent = default_agent
        self._loop = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create the event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        return self._loop

    def _emit_event_sync(
        self, event_type: str, agent_name: str, payload: dict[str, Any] | None = None
    ):
        """Synchronously emit an event to the queue."""
        event = {
            "event_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "agent_id": agent_name,
            "data": payload or {},
        }

        loop = self._get_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(self.queue.put(event), loop)
        else:
            self.queue.put_nowait(event)

    async def _emit_event(
        self, event_type: str, agent_name: str, payload: dict[str, Any] | None = None
    ):
        """Asynchronously emit an event to the queue."""
        event = {
            "event_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "agent_id": agent_name,
            "data": payload or {},
        }
        await self.queue.put(event)

    # --- Synchronous Callback Methods (for sync execution) ---

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Triggered when the model receives a prompt and starts processing.
        Visual: Thought bubble '...' appears over the character.
        """
        metadata = metadata or {}
        agent_name = metadata.get("agent_name", self.current_active_agent)
        self.current_active_agent = agent_name

        self._emit_event_sync(
            GameEventType.AGENT_THINK_START, agent_name, {"status": "processing"}
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Triggered when the model has finished generating a response.
        Visual: Speech bubble with the response text.
        """
        text_content = ""
        if response.generations:
            generation = response.generations[0][0]
            if isinstance(generation, ChatGeneration):
                text_content = generation.message.content
            else:
                text_content = generation.text

        self._emit_event_sync(
            GameEventType.AGENT_SPEAK,
            self.current_active_agent,
            {"content": text_content},
        )

        self._emit_event_sync(GameEventType.AGENT_IDLE, self.current_active_agent)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Triggered when an agent decides to use a tool.
        Visual: Character shows an icon (e.g., magnifying glass for web search).
        """
        tool_name = serialized.get("name", "generic_tool")
        metadata = metadata or {}
        agent_name = metadata.get("agent_name", self.current_active_agent)

        self._emit_event_sync(
            GameEventType.TOOL_START,
            agent_name,
            {"tool_name": tool_name, "input_args": input_str[:100]},
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Triggered when a tool finishes its work.
        Visual: Icon disappears or character nods.
        """
        self._emit_event_sync(
            GameEventType.TOOL_END,
            self.current_active_agent,
            {"result_preview": output[:50] + "..." if len(output) > 50 else output},
        )

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Triggered when an error occurs in the chain."""
        self._emit_event_sync(
            GameEventType.ERROR,
            self.current_active_agent,
            {"error": str(error)},
        )
