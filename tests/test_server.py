"""Tests for GameServer."""

import pytest
from fastapi.testclient import TestClient

from pixelgraph.server import GameServer, SessionManager
from pixelgraph.schemas.events import VisualConfig, AgentConfig


class TestSessionManager:
    """Tests for the SessionManager class."""

    def test_create_session(self):
        """Creating a session should return a queue."""
        manager = SessionManager()
        queue = manager.create_session("test_id", None)

        assert queue is not None
        assert "test_id" in manager.sessions

    def test_get_session(self):
        """Getting a session should return the correct data."""
        manager = SessionManager()
        manager.create_session("test_id", None)

        session = manager.get_session("test_id")
        assert session is not None
        assert "queue" in session

    def test_remove_session(self):
        """Removing a session should clean it up."""
        manager = SessionManager()
        manager.create_session("test_id", None)
        manager.remove_session("test_id")

        assert "test_id" not in manager.sessions


class TestGameServer:
    """Tests for the GameServer class."""

    def test_server_initializes_without_graph(self):
        """Server should initialize in demo mode without a graph."""
        server = GameServer(graph=None, title="Test")
        assert server.graph is None
        assert server.title == "Test"

    def test_server_accepts_visual_config(self):
        """Server should accept a VisualConfig object."""
        config = VisualConfig(
            title="Test",
            nodes={"agent1": AgentConfig(sprite="wizard")}
        )
        server = GameServer(graph=None, config=config)
        assert server.config.title == "Test"

    def test_server_accepts_dict_config(self):
        """Server should accept a dict config and convert it."""
        config = {
            "title": "Test Dict",
            "theme": "dungeon",
            "nodes": {}
        }
        server = GameServer(graph=None, config=config)
        assert server.config.title == "Test Dict"
        assert server.config.theme == "dungeon"

    def test_health_endpoint(self):
        """Health endpoint should return status."""
        server = GameServer(graph=None, title="Test")
        client = TestClient(server.app)

        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_config_endpoint(self):
        """Config endpoint should return visual config."""
        config = VisualConfig(title="My Title", theme="scifi")
        server = GameServer(graph=None, config=config)
        client = TestClient(server.app)

        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My Title"
        assert data["theme"] == "scifi"
