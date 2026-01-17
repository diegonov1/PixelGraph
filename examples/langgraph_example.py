"""
LangGraph Example - Full integration with a real LangGraph

This example shows how to integrate LangArcade with an actual
LangGraph application. Requires OPENAI_API_KEY environment variable.

Usage:
    export OPENAI_API_KEY=your-api-key
    python examples/langgraph_example.py

Then open the frontend to interact with the agent.
"""

import os
import sys
sys.path.insert(0, '.')

from typing import Annotated, TypedDict

try:
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
except ImportError:
    print("This example requires langchain-openai and langgraph.")
    print("Install with: pip install langchain-openai langgraph")
    sys.exit(1)

from langarcade import GameServer
from langarcade.schemas.events import VisualConfig, AgentConfig


# Define the state for our graph
class State(TypedDict):
    messages: Annotated[list, add_messages]


def create_graph():
    """Create a simple conversational agent graph."""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Using demo mode.")
        return None

    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
    )

    # Define the chatbot node
    def chatbot(state: State):
        """Simple chatbot that responds to messages."""
        return {"messages": [llm.invoke(state["messages"])]}

    # Build the graph
    graph = StateGraph(State)
    graph.add_node("chatbot", chatbot)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)

    return graph.compile()


def main():
    # Create the LangGraph application
    app = create_graph()

    # Configure visual appearance
    config = VisualConfig(
        title="LangGraph Chat",
        theme="dungeon",
        nodes={
            "chatbot": AgentConfig(
                sprite="wizard",
                color="blue",
                display_name="AI Assistant"
            )
        }
    )

    # Create the GameServer
    server = GameServer(
        graph=app,
        config=config,
        title="LangGraph Chat Demo"
    )

    print("\n" + "=" * 50)
    print("  LangGraph Chat Demo")
    print("=" * 50)
    print("\n  Backend: http://localhost:8000")
    print("  Frontend: Run 'npm run dev' in frontend/ folder")
    print("\n  Type messages to chat with the AI!\n")

    server.serve(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
