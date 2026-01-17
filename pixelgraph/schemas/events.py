"""Event schemas for the WebSocket protocol."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events sent to the frontend."""

    # Agent lifecycle events
    AGENT_THINK_START = "AGENT_THINK_START"
    AGENT_SPEAK = "AGENT_SPEAK"
    AGENT_IDLE = "AGENT_IDLE"

    # Tool events
    TOOL_START = "TOOL_START"
    TOOL_END = "TOOL_END"

    # System events
    SYSTEM_INIT = "SYSTEM_INIT"
    SYSTEM_READY = "SYSTEM_READY"
    SIMULATION_START = "SIMULATION_START"
    SIMULATION_END = "SIMULATION_END"

    # Error events
    ERROR = "ERROR"


class GameEvent(BaseModel):
    """Standard event structure for WebSocket communication."""

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: EventType
    agent_id: str = "system"
    data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class AgentConfig(BaseModel):
    """Visual configuration for an agent."""

    sprite: str = "wizard"
    color: str = "blue"
    scale: float = 1.0
    display_name: Optional[str] = None


class VisualConfig(BaseModel):
    """Complete visual configuration for the game."""

    nodes: dict[str, AgentConfig] = Field(default_factory=dict)
    theme: str = "dungeon"
    title: str = "LangArcade"
