#!/usr/bin/env python3
"""
Test script for the remote Gong MCP server.
This script helps you:
1. Register an OAuth client
2. Test the OAuth flow
3. Test MCP tools with authentication
"""

import requests
import json
import sys

BASE_URL = "https://gong-mcp.stag.daloopa.com"

def test_health():
    """Test that the server is running."""
    print("Testing server health...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200

def register_client(client_name="Claude Desktop Client"):
    """Register a new OAuth client."""
    print(f"Registering OAuth client: {client_name}")

    data = {
        "client_name": client_name,
        "redirect_uris": [
            "http://localhost:3000/callback",
            "claude://oauth/callback"  # For Claude Desktop
        ],
        "token_endpoint_auth_method": "client_secret_post"
    }

    response = requests.post(f"{BASE_URL}/register", json=data)

    if response.status_code == 200:
        client_info = response.json()
        print("✅ Client registered successfully!")
        print(json.dumps(client_info, indent=2))
        print("\n" + "="*60)
        print("SAVE THESE CREDENTIALS - YOU'LL NEED THEM FOR CLAUDE:")
        print("="*60)
        print(f"Client ID: {client_info['client_id']}")
        print(f"Client Secret: {client_info['client_secret']}")
        print("="*60 + "\n")
        return client_info
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return None

def get_oauth_config():
    """Get OAuth configuration."""
    print("Fetching OAuth configuration...")
    response = requests.get(f"{BASE_URL}/.well-known/oauth-authorization-server")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        config = response.json()
        print(json.dumps(config, indent=2))
        print()
        return config
    return None

def test_mcp_endpoint_without_auth():
    """Test MCP endpoint without authentication (should fail)."""
    print("Testing MCP endpoint without authentication...")
    response = requests.post(
        f"{BASE_URL}/server/mcp/",
        json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly requires authentication\n")
        return True
    else:
        print(f"⚠️  Unexpected response: {response.text}\n")
        return False

def generate_claude_config(client_id, client_secret):
    """Generate Claude Desktop configuration."""
    config = {
        "mcpServers": {
            "gong": {
                "url": f"{BASE_URL}/server/mcp/",
                "transport": "streamable-http",
                "auth": {
                    "type": "oauth2",
                    "authorization_url": f"{BASE_URL}/authorize",
                    "token_url": f"{BASE_URL}/token",
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            }
        }
    }

    print("\n" + "="*60)
    print("CLAUDE DESKTOP CONFIGURATION:")
    print("="*60)
    print("Add this to your Claude Desktop MCP settings:")
    print(json.dumps(config, indent=2))
    print("="*60 + "\n")

    # Also save to file
    with open("claude_mcp_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("✅ Configuration saved to: claude_mcp_config.json\n")

def main():
    print("="*60)
    print("Gong MCP Remote Server Test")
    print("="*60 + "\n")

    # Test 1: Health check
    if not test_health():
        print("❌ Server is not responding. Check the URL and try again.")
        sys.exit(1)

    # Test 2: OAuth config
    oauth_config = get_oauth_config()
    if not oauth_config:
        print("❌ Could not fetch OAuth configuration.")
        sys.exit(1)

    # Test 3: MCP endpoint security
    test_mcp_endpoint_without_auth()

    # Test 4: Register client
    print("Do you want to register a new OAuth client? (y/n): ", end="")
    if input().lower().strip() == 'y':
        client_name = input("Enter client name (default: Claude Desktop Client): ").strip()
        if not client_name:
            client_name = "Claude Desktop Client"

        client_info = register_client(client_name)
        if client_info:
            generate_claude_config(client_info['client_id'], client_info['client_secret'])

            print("\n📝 NEXT STEPS:")
            print("1. Save your client_id and client_secret in a secure location")
            print("2. Add the configuration to Claude Desktop:")
            print("   - Open Claude Desktop settings")
            print("   - Go to Developer > Edit Config")
            print("   - Add the configuration from claude_mcp_config.json")
            print("3. Restart Claude Desktop")
            print("4. You'll be prompted to login when Claude tries to use the MCP server")
    else:
        print("\nTo test with existing credentials:")
        print("1. Run this script again and register a client, OR")
        print("2. If you already have client credentials, use generate_claude_config() manually")

    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()
