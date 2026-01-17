# PixelGraph

> 8-bit visualization for LangGraph agents

PixelGraph transforms your LangGraph agent interactions into a retro 8-bit game experience. Watch your AI agents think, speak, and use tools in a nostalgic pixel-art environment.

## Features

- **Drop-in Integration**: Works with any existing LangGraph application
- **Real-time Visualization**: See agent thoughts, speech, and tool usage
- **8-bit Aesthetics**: Pixel art sprites and retro styling
- **WebSocket Communication**: Bidirectional real-time updates
- **Action Queue**: Smooth animation sequencing regardless of event speed

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/diegonov1/PixelGraph.git
cd PixelGraph

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Run Demo Mode

Without any LLM API key, you can run the demo:

```bash
# Terminal 1: Start backend
python examples/simple_demo.py

# Terminal 2: Start frontend
cd frontend && npm run dev
```

Open http://localhost:3000 in your browser.

### Run with LangGraph

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key

# Run the LangGraph example
python examples/langgraph_example.py
```

## Usage

Integrate PixelGraph with your existing LangGraph application:

```python
from langgraph.graph import StateGraph
from pixelgraph import GameServer

# Your existing LangGraph code
graph = StateGraph(State)
# ... add nodes and edges ...
app = graph.compile()

# Add visualization with one line
server = GameServer(app)
server.serve()
```

### Visual Configuration

Customize how agents appear in the game:

```python
from pixelgraph import GameServer
from pixelgraph.schemas.events import VisualConfig, AgentConfig

config = VisualConfig(
    title="My Agent Team",
    theme="dungeon",
    nodes={
        "researcher": AgentConfig(sprite="wizard", color="blue"),
        "writer": AgentConfig(sprite="bard", color="red"),
    }
)

server = GameServer(app, config=config)
server.serve()
```

## Architecture

```
Frontend (React + Phaser)     Backend (FastAPI + LangGraph)
     ┌─────────────┐              ┌─────────────┐
     │   Phaser    │◄─WebSocket──►│  GameServer │
     │   Canvas    │              │             │
     └─────────────┘              │  Callback   │
     ┌─────────────┐              │   Handler   │
     │   React     │              │      ▲      │
     │   HUD/Log   │              │      │      │
     └─────────────┘              │  LangGraph  │
                                  └─────────────┘
```

### Event Flow

1. LangGraph emits events during execution
2. `GameVisualizerCallbackHandler` captures and transforms events
3. Events are sent via WebSocket to the frontend
4. Frontend queues events in the `ActionQueue`
5. Phaser consumes events one at a time, playing animations

## Development

### Project Structure

```
pixelgraph/
├── pixelgraph/          # Python package
│   ├── __init__.py      # Package exports
│   ├── callback.py      # LangChain callback handler
│   ├── server.py        # FastAPI WebSocket server
│   ├── schemas/         # Pydantic event schemas
│   └── static/          # Built frontend (after npm build)
├── frontend/            # React + Phaser frontend
│   ├── src/
│   │   ├── game/        # Phaser logic
│   │   │   ├── scenes/  # Game scenes
│   │   │   ├── entities/# Sprite classes
│   │   │   └── systems/ # Event bus, action queue
│   │   └── components/  # React UI components
│   └── public/assets/   # Sprites and assets
├── examples/            # Usage examples
└── tests/               # Test suite
```

### Commands

```bash
make install      # Install all dependencies
make dev          # Run both backend and frontend
make build        # Build frontend for production
make test         # Run tests
make docker-dev   # Run with Docker (development)
make docker-prod  # Run with Docker (production)
```

## Roadmap

- [ ] Multi-agent support with dynamic positioning
- [ ] Tool-specific animations (search, calculator, etc.)
- [ ] Speed control for event playback
- [ ] Custom sprite support
- [ ] Themes (dungeon, sci-fi, city)
- [ ] Export conversation as GIF

## License

MIT

## Contributing

Contributions welcome! Please read our contributing guidelines first.
