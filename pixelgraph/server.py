"""
GameServer - FastAPI WebSocket server for PixelGraph.

This module provides the main server class that accepts a compiled LangGraph
and serves both the WebSocket API and the static frontend files.
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pixelgraph.callback import GameVisualizerCallbackHandler, GameEventType
from pixelgraph.schemas.events import VisualConfig, AgentConfig


class SessionManager:
    """Manages active WebSocket sessions and their associated graph instances."""

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, session_id: str, websocket: WebSocket) -> asyncio.Queue:
        """Create a new session with an event queue."""
        event_queue = asyncio.Queue()
        self.sessions[session_id] = {
            "websocket": websocket,
            "queue": event_queue,
            "active": True,
        }
        return event_queue

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str):
        """Remove a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["active"] = False
            del self.sessions[session_id]


class GameServer:
    """
    Main server class for PixelGraph visualization.

    This server accepts a compiled LangGraph application and serves:
    - WebSocket endpoint for real-time communication
    - Static files for the 8-bit frontend

    Usage:
        from langgraph.graph import StateGraph
        from pixelgraph import GameServer

        # Define your graph
        graph = StateGraph(State)
        # ... add nodes and edges ...
        app = graph.compile()

        # Create and run the visualizer
        server = GameServer(app)
        server.serve()
    """

    def __init__(
        self,
        graph: Any = None,
        config: Optional[VisualConfig | dict] = None,
        title: str = "PixelGraph",
    ):
        """
        Initialize the GameServer.

        Args:
            graph: Compiled LangGraph application (optional, can be set later)
            config: Visual configuration for agents and theme
            title: Title displayed in the frontend
        """
        self.graph = graph
        self.title = title

        # Parse config
        if config is None:
            self.config = VisualConfig(title=title)
        elif isinstance(config, dict):
            self.config = VisualConfig(**config)
        else:
            self.config = config

        self.session_manager = SessionManager()
        self._setup_app()

    def _setup_app(self):
        """Set up the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            print(f"\n{'='*50}")
            print(f"  PixelGraph - {self.title}")
            print(f"{'='*50}")
            print(f"  Frontend: http://localhost:{{port}}")
            print(f"  WebSocket: ws://localhost:{{port}}/ws/game")
            print(f"{'='*50}\n")
            yield
            # Shutdown

        self.app = FastAPI(
            title=self.title,
            description="PixelGraph - 8-bit visualization for LangGraph agents",
            lifespan=lifespan,
        )

        # API routes
        @self.app.get("/api/config")
        async def get_config():
            """Return the visual configuration."""
            return self.config.model_dump()

        @self.app.get("/api/health")
        async def health():
            """Health check endpoint."""
            return {"status": "ok", "title": self.title}

        @self.app.websocket("/ws/game")
        async def websocket_endpoint(websocket: WebSocket):
            """Main WebSocket endpoint for game communication."""
            await websocket.accept()
            session_id = str(id(websocket))
            event_queue = self.session_manager.create_session(session_id, websocket)

            # Create callback handler for this session
            callback_handler = GameVisualizerCallbackHandler(event_queue)

            # Background task to send events from queue to WebSocket
            async def sender_task():
                try:
                    while self.session_manager.get_session(session_id):
                        try:
                            event = await asyncio.wait_for(
                                event_queue.get(), timeout=0.1
                            )
                            await websocket.send_json(event)
                        except asyncio.TimeoutError:
                            continue
                except Exception:
                    pass

            sender = asyncio.create_task(sender_task())

            # Send initial system ready event
            await event_queue.put(
                {
                    "event_id": "init",
                    "timestamp": "now",
                    "type": "SYSTEM_READY",
                    "agent_id": "system",
                    "data": {
                        "config": self.config.model_dump(),
                        "message": "PixelGraph ready!",
                    },
                }
            )

            try:
                while True:
                    # Receive messages from frontend
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "START_SIMULATION":
                        # Execute the graph with the callback handler
                        user_input = message.get("input", "Hello!")

                        await event_queue.put(
                            {
                                "event_id": "sim_start",
                                "timestamp": "now",
                                "type": "SIMULATION_START",
                                "agent_id": "system",
                                "data": {"input": user_input},
                            }
                        )

                        if self.graph is not None:
                            try:
                                # Run the graph with our callback
                                config = {
                                    "callbacks": [callback_handler],
                                    "metadata": {"agent_name": "agent"},
                                }

                                # Check if graph has ainvoke (async) or invoke (sync)
                                if hasattr(self.graph, "ainvoke"):
                                    result = await self.graph.ainvoke(
                                        {"messages": [("user", user_input)]},
                                        config=config,
                                    )
                                elif hasattr(self.graph, "invoke"):
                                    result = self.graph.invoke(
                                        {"messages": [("user", user_input)]},
                                        config=config,
                                    )
                                else:
                                    result = {"error": "Graph has no invoke method"}

                                await event_queue.put(
                                    {
                                        "event_id": "sim_end",
                                        "timestamp": "now",
                                        "type": "SIMULATION_END",
                                        "agent_id": "system",
                                        "data": {"result": str(result)[:200]},
                                    }
                                )
                            except Exception as e:
                                await event_queue.put(
                                    {
                                        "event_id": "error",
                                        "timestamp": "now",
                                        "type": "ERROR",
                                        "agent_id": "system",
                                        "data": {"error": str(e)},
                                    }
                                )
                        else:
                            # Demo mode: send a sample response
                            await asyncio.sleep(0.5)
                            await event_queue.put(
                                {
                                    "event_id": "demo_think",
                                    "timestamp": "now",
                                    "type": "AGENT_THINK_START",
                                    "agent_id": "wizard",
                                    "data": {"status": "processing"},
                                }
                            )
                            await asyncio.sleep(1)
                            await event_queue.put(
                                {
                                    "event_id": "demo_speak",
                                    "timestamp": "now",
                                    "type": "AGENT_SPEAK",
                                    "agent_id": "wizard",
                                    "data": {
                                        "content": f"Greetings, traveler! You said: '{user_input}'"
                                    },
                                }
                            )
                            await asyncio.sleep(0.3)
                            await event_queue.put(
                                {
                                    "event_id": "demo_idle",
                                    "timestamp": "now",
                                    "type": "AGENT_IDLE",
                                    "agent_id": "wizard",
                                    "data": {},
                                }
                            )
                            await event_queue.put(
                                {
                                    "event_id": "sim_end",
                                    "timestamp": "now",
                                    "type": "SIMULATION_END",
                                    "agent_id": "system",
                                    "data": {"result": "Demo completed"},
                                }
                            )

            except WebSocketDisconnect:
                self.session_manager.remove_session(session_id)
                sender.cancel()
            except Exception as e:
                print(f"WebSocket error: {e}")
                self.session_manager.remove_session(session_id)
                sender.cancel()

        # Mount static files (frontend build)
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists() and (static_dir / "index.html").exists():
            # Serve frontend from package
            @self.app.get("/")
            async def serve_frontend():
                return FileResponse(static_dir / "index.html")

            self.app.mount(
                "/", StaticFiles(directory=str(static_dir), html=True), name="static"
            )
        else:
            # Development mode - frontend served separately
            @self.app.get("/")
            async def dev_info():
                return {
                    "message": "PixelGraph API Server",
                    "note": "Frontend not bundled. Run frontend dev server separately.",
                    "websocket": "/ws/game",
                    "config": "/api/config",
                }

    def serve(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """
        Start the server.

        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional arguments passed to uvicorn
        """
        print(f"\nStarting PixelGraph on http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port, **kwargs)

    async def serve_async(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Start the server asynchronously."""
        config = uvicorn.Config(self.app, host=host, port=port, **kwargs)
        server = uvicorn.Server(config)
        await server.serve()
