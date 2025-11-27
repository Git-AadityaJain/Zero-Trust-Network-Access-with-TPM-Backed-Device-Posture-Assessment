#!/usr/bin/env python3
"""
Start the DPA Local API Server

This script starts the DPA API server that exposes challenge signing endpoints
for the frontend to use.

Usage:
    python start_api_server.py [--host 127.0.0.1] [--port 8081]
"""

import sys
import os
from pathlib import Path

# Add project root to path so we can import 'dpa' module
# Same pattern as other CLI scripts (enroll_cli.py, etc.)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dpa.api.server import start_server
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start DPA Local API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", 
                       help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8081, 
                       help="Port to bind to (default: 8081)")
    parser.add_argument("--log-level", type=str, default="info",
                       choices=["debug", "info", "warning", "error"],
                       help="Logging level (default: info)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DPA Local API Server")
    print("=" * 60)
    print(f"Starting server on {args.host}:{args.port}")
    print(f"Log level: {args.log_level}")
    print("=" * 60)
    print()
    
    try:
        start_server(host=args.host, port=args.port, log_level=args.log_level)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)

