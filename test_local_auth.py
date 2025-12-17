#!/usr/bin/env python3
"""
Local testing script for the simplified Gong MCP server.
Tests HTTP Basic Auth with Gong credentials.
"""

import base64
import requests
import json
import sys

# Local server URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint (no auth required)."""
    print("=" * 60)
    print("TEST 1: Health Check (No Auth)")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

    return response.status_code == 200

def test_mcp_no_auth():
    """Test MCP endpoint without authentication (should fail)."""
    print("=" * 60)
    print("TEST 2: MCP Endpoint Without Auth (Should Fail)")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/server/mcp/",
        json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}\n")

    return response.status_code == 401

def test_mcp_with_auth(access_key: str, access_secret: str):
    """Test MCP endpoint with HTTP Basic Auth."""
    print("=" * 60)
    print("TEST 3: MCP Endpoint With Auth")
    print("=" * 60)

    # Create Basic Auth header
    credentials = f"{access_key}:{access_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    print(f"Using credentials:")
    print(f"  Access Key: {access_key[:20]}...")
    print(f"  Access Secret: {access_secret[:20]}...")

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    # Test initialize request
    response = requests.post(
        f"{BASE_URL}/server/mcp/",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Authentication successful!")
        try:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        except:
            print(f"Response (not JSON): {response.text[:500]}")
    else:
        print(f"❌ Failed: {response.text}\n")
        return False

    return response.status_code == 200

def test_list_calls(access_key: str, access_secret: str):
    """Test list_calls tool."""
    print("\n" + "=" * 60)
    print("TEST 4: List Calls Tool")
    print("=" * 60)

    credentials = f"{access_key}:{access_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    # Test list_calls tool
    response = requests.post(
        f"{BASE_URL}/server/mcp/",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "list_calls",
                "arguments": {}
            },
            "id": 2
        }
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Tool call successful!")
        try:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2)[:1000] + "...")
        except:
            print(f"Response: {response.text[:500]}")
    else:
        print(f"❌ Failed: {response.text}\n")
        return False

    return response.status_code == 200

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GONG MCP SERVER - LOCAL AUTHENTICATION TEST")
    print("=" * 60 + "\n")

    print("Make sure the server is running locally:")
    print("  uvicorn app.server:app --reload")
    print("\nPress Enter to continue, or Ctrl+C to exit...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(0)

    # Test 1: Health check
    if not test_health():
        print("❌ Server not responding. Make sure it's running!")
        sys.exit(1)

    # Test 2: No auth (should fail)
    if not test_mcp_no_auth():
        print("❌ Server should require authentication!")
        sys.exit(1)

    # Test 3 & 4: With authentication
    print("\nEnter your Gong API credentials for testing:")
    print("(You can find these in your Gong account settings)")

    access_key = input("Gong Access Key: ").strip()
    if not access_key:
        # Use credentials from production.env for testing
        print("\nNo credentials provided. Looking for credentials in production.env...")
        try:
            from dotenv import load_dotenv
            import os
            load_dotenv('production.env')
            access_key = os.getenv("GONG_ACCESS_KEY")
            access_secret = os.getenv("GONG_ACCESS_SECRET")

            if access_key and access_secret:
                print(f"✅ Found credentials in production.env")
                print(f"   Access Key: {access_key[:20]}...")
            else:
                print("❌ No credentials found. Exiting.")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            sys.exit(1)
    else:
        access_secret = input("Gong Access Secret: ").strip()

    # Test with auth
    if not test_mcp_with_auth(access_key, access_secret):
        print("\n❌ Authentication test failed!")
        sys.exit(1)

    # Test list_calls tool
    if not test_list_calls(access_key, access_secret):
        print("\n❌ Tool call test failed!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour server is ready to deploy!")
    print("Users can now connect using their Gong credentials.")

if __name__ == "__main__":
    main()
