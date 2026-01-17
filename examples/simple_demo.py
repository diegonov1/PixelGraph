"""
Simple Demo - Run PixelGraph without a real LangGraph

This example demonstrates the visualization without requiring
any LLM API keys. The server runs in "demo mode" and sends
simulated events.

Usage:
    python examples/simple_demo.py

Then open http://localhost:8000 in your browser (or run frontend separately)
"""

import sys
sys.path.insert(0, '.')

from pixelgraph import GameServer
from pixelgraph.schemas.events import VisualConfig, AgentConfig


def main():
    # Configure the visual appearance
    config = VisualConfig(
        title="PixelGraph Demo",
        theme="dungeon",
        nodes={
            "wizard": AgentConfig(
                sprite="wizard",
                color="purple",
                display_name="Wise Wizard"
            )
        }
    )

    # Create server without a real LangGraph (demo mode)
    server = GameServer(
        graph=None,  # No real graph = demo mode
        config=config,
        title="PixelGraph Demo"
    )

    print("\n" + "=" * 50)
    print("  PixelGraph Demo Server")
    print("=" * 50)
    print("\n  Backend: http://localhost:8000")
    print("  Frontend: Run 'npm run dev' in frontend/ folder")
    print("            or visit http://localhost:8000 if frontend is built")
    print("\n  Send messages in the frontend to see the demo!\n")

    server.serve(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
