"""
PixelGraph - 8-bit visualization for LangGraph agents

A drop-in visualization library that transforms your LangGraph
agent interactions into an 8-bit game experience.
"""

from pixelgraph.server import GameServer
from pixelgraph.callback import GameVisualizerCallbackHandler, GameEventType

__version__ = "0.1.0"
__all__ = ["GameServer", "GameVisualizerCallbackHandler", "GameEventType"]
