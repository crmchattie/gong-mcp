#!/usr/bin/env python3

"""
Development script for the Gong MCP server.
Provides convenient commands for development and testing.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main development script."""
    if len(sys.argv) < 2:
        print(
            """
🚀 Gong MCP Server Development Script

Usage:
  python dev.py <command>

Commands:
  test        - Run all tests
  lint        - Run linting (ruff)
  format      - Format code (black)
  server      - Start the MCP server
  install     - Install dependencies
  clean       - Clean up cache files
  help        - Show this help message

Examples:
  python dev.py test
  python dev.py server
  python dev.py lint
        """
        )
        return

    command = sys.argv[1].lower()

    if command == "test":
        success = True
        success &= run_command(
            "uv run python test_gong_client.py", "Running core tests"
        )
        success &= run_command(
            "uv run python test_final_check.py", "Running verification tests"
        )
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)

    elif command == "lint":
        run_command("uv run ruff check .", "Running linting")

    elif command == "format":
        run_command("uv run black .", "Formatting code")

    elif command == "server":
        print("🚀 Starting Gong MCP server...")
        print(
            "Note: Make sure to set GONG_ACCESS_KEY and GONG_ACCESS_SECRET environment variables"
        )
        print("Press Ctrl+C to stop the server")
        try:
            subprocess.run(["uv", "run", "gong_server.py"], check=True)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
        except subprocess.CalledProcessError as e:
            print(f"❌ Server failed to start: {e}")
            sys.exit(1)

    elif command == "install":
        run_command("uv sync", "Installing dependencies")
        run_command("uv sync --extra dev", "Installing development dependencies")

    elif command == "clean":
        # Clean up Python cache files
        cache_dirs = [".pytest_cache", "__pycache__"]
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                import shutil

                shutil.rmtree(cache_dir)
                print(f"🧹 Cleaned {cache_dir}")

        # Clean up .pyc files
        for pyc_file in Path(".").rglob("*.pyc"):
            pyc_file.unlink()
            print(f"🧹 Cleaned {pyc_file}")

        print("✅ Cleanup completed")

    elif command == "help":
        main()  # Show help again

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python dev.py help' for available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
