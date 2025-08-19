#!/usr/bin/env python3
"""
Launcher script for Gong MCP server.
This script activates the virtual environment and runs the server.
"""
import os
import sys
import subprocess

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the virtual environment python
venv_python = os.path.join(script_dir, '.venv', 'bin', 'python')

# Path to the main server file
server_file = os.path.join(script_dir, 'gong_server.py')

# Check if virtual environment exists
if not os.path.exists(venv_python):
    print("Error: Virtual environment not found. Please run 'uv sync' first.", file=sys.stderr)
    sys.exit(1)

# Run the server using the virtual environment python
try:
    subprocess.run([venv_python, server_file], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error running server: {e}", file=sys.stderr)
    sys.exit(1)
except KeyboardInterrupt:
    print("Server stopped by user", file=sys.stderr)
    sys.exit(0)
