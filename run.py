#!/usr/bin/env python3
"""
Convenience script to run the FastAPI application.

Usage:
    python run.py              # Production mode
    python run.py --dev        # Development mode with reload
    python run.py --debug      # Debug mode with reload and verbose logging
"""
import sys
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the Pharo Reviewer Agent API")
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with auto-reload"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode with auto-reload and verbose logging"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (production only, default: 1)"
    )

    args = parser.parse_args()

    # Development/Debug mode
    if args.dev or args.debug:
        log_level = "debug" if args.debug else "info"
        print(f"🚀 Starting in {'DEBUG' if args.debug else 'DEVELOPMENT'} mode...")
        print(f"📍 API: http://{args.host}:{args.port}")
        print(f"📖 Docs: http://{args.host}:{args.port}/docs")
        print(f"🔄 Auto-reload: enabled")
        print()

        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level=log_level
        )

    # Production mode
    else:
        print(f"🚀 Starting in PRODUCTION mode...")
        print(f"📍 API: http://{args.host}:{args.port}")
        print(f"👷 Workers: {args.workers}")
        print()

        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info"
        )


if __name__ == "__main__":
    main()
