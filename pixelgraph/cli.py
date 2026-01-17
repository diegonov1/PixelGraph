"""
PixelGraph CLI - Command line interface for running the visualizer.

Usage:
    pixelgraph run my_script.py:app
    pixelgraph demo
"""

import argparse
import importlib.util
import sys
from pathlib import Path

from pixelgraph.server import GameServer
from pixelgraph.schemas.events import VisualConfig


def load_app_from_string(app_string: str):
    """
    Load a LangGraph app from a module:attribute string.

    Format: "path/to/module.py:app_name" or "module.name:app_name"
    """
    if ':' not in app_string:
        raise ValueError(
            f"Invalid app string: {app_string}. "
            "Expected format: 'module.py:app' or 'module.name:app'"
        )

    module_path, app_name = app_string.rsplit(':', 1)

    # Check if it's a file path
    if module_path.endswith('.py'):
        path = Path(module_path)
        if not path.exists():
            raise FileNotFoundError(f"Module file not found: {module_path}")

        spec = importlib.util.spec_from_file_location("user_module", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["user_module"] = module
        spec.loader.exec_module(module)
    else:
        # It's a module name
        module = importlib.import_module(module_path)

    if not hasattr(module, app_name):
        raise AttributeError(
            f"Module {module_path} has no attribute '{app_name}'"
        )

    return getattr(module, app_name)


def run_command(args):
    """Run a LangGraph app with visualization."""
    try:
        app = load_app_from_string(args.app)
    except Exception as e:
        print(f"Error loading app: {e}")
        sys.exit(1)

    config = VisualConfig(title=args.title or "PixelGraph")

    server = GameServer(
        graph=app,
        config=config,
        title=args.title or "PixelGraph"
    )

    server.serve(host=args.host, port=args.port)


def demo_command(args):
    """Run demo mode without a real LangGraph."""
    config = VisualConfig(title="PixelGraph Demo")

    server = GameServer(
        graph=None,
        config=config,
        title="PixelGraph Demo"
    )

    print("\n" + "=" * 50)
    print("  PixelGraph Demo Mode")
    print("=" * 50)
    print(f"\n  Open http://{args.host}:{args.port} in your browser")
    print("  (Make sure frontend is running on port 3000)")
    print("\n" + "=" * 50 + "\n")

    server.serve(host=args.host, port=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="PixelGraph - 8-bit visualization for LangGraph agents"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser(
        "run", help="Run a LangGraph app with visualization"
    )
    run_parser.add_argument(
        "app",
        help="App to run in format 'module.py:app' or 'module.name:app'"
    )
    run_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)"
    )
    run_parser.add_argument(
        "--port", "-p", type=int, default=8000, help="Port to bind (default: 8000)"
    )
    run_parser.add_argument(
        "--title", "-t", help="Title for the visualizer"
    )
    run_parser.set_defaults(func=run_command)

    # Demo command
    demo_parser = subparsers.add_parser(
        "demo", help="Run demo mode without a real LangGraph"
    )
    demo_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)"
    )
    demo_parser.add_argument(
        "--port", "-p", type=int, default=8000, help="Port to bind (default: 8000)"
    )
    demo_parser.set_defaults(func=demo_command)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
