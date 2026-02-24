"""Standalone entry point for the packaged Python backend."""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="c0lor-mem backend")
    parser.add_argument("--port", type=int, default=18100, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
