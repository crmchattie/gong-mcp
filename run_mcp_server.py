#!/usr/bin/env python3
"""
Run the Gong MCP server for testing with MCP Inspector
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from production.env
load_dotenv('production.env')

# Add the current directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the MCP server
from app.gong_mcp import gong_mcp

if __name__ == "__main__":
    # Run the server with stdio transport (required for MCP Inspector)
    gong_mcp.run(transport='stdio')
