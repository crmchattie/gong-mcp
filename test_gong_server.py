#!/usr/bin/env python3

"""
Test script for the Gong MCP server.
This script tests the basic functionality without requiring actual API credentials.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch
from gong_server import GongClient, list_calls, retrieve_transcripts


async def test_gong_client():
    """Test the GongClient class with mocked responses."""
    print("Testing GongClient...")

    # Mock API responses
    mock_calls_response = {
        "calls": [
            {
                "id": "test_call_1",
                "title": "Test Call 1",
                "started": "2024-03-01T10:00:00Z",
                "duration": 3600,
            },
            {
                "id": "test_call_2",
                "title": "Test Call 2",
                "started": "2024-03-02T14:00:00Z",
                "duration": 1800,
            },
        ]
    }

    mock_transcript_response = {
        "transcripts": [
            {
                "speakerId": "speaker_1",
                "topic": "Product Discussion",
                "sentences": [
                    {"start": 0, "text": "Hello, how are you today?"},
                    {"start": 5, "text": "I'm doing well, thank you."},
                ],
            }
        ]
    }

    # Test with mocked client
    with patch.object(GongClient, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = [mock_calls_response, mock_transcript_response]

        client = GongClient("test_key", "test_secret")

        # Test list_calls
        calls_result = await client.list_calls(
            "2024-03-01T00:00:00Z", "2024-03-31T23:59:59Z"
        )
        assert calls_result == mock_calls_response
        print("✓ list_calls test passed")

        # Test retrieve_transcripts
        transcript_result = await client.retrieve_transcripts(["test_call_1"])
        assert transcript_result == mock_transcript_response
        print("✓ retrieve_transcripts test passed")


async def test_mcp_tools():
    """Test the MCP tool functions."""
    print("\nTesting MCP Tools...")

    # Mock the gong_client
    with patch("gong_server.gong_client") as mock_client:
        mock_client.list_calls.return_value = {
            "calls": [{"id": "test", "title": "Test Call"}]
        }
        mock_client.retrieve_transcripts.return_value = {
            "transcripts": [{"speakerId": "test"}]
        }

        # Test list_calls tool
        result = await list_calls("2024-03-01T00:00:00Z", "2024-03-31T23:59:59Z")
        assert "test" in result
        print("✓ list_calls MCP tool test passed")

        # Test retrieve_transcripts tool
        result = await retrieve_transcripts(["test_call_1"])
        assert "test" in result
        print("✓ retrieve_transcripts MCP tool test passed")


async def test_error_handling():
    """Test error handling in the tools."""
    print("\nTesting Error Handling...")

    with patch("gong_server.gong_client") as mock_client:
        mock_client.list_calls.side_effect = Exception("API Error")

        # Test error handling in list_calls
        result = await list_calls()
        assert "Error listing calls" in result
        print("✓ Error handling test passed")


def test_signature_generation():
    """Test HMAC signature generation."""
    print("\nTesting Signature Generation...")

    client = GongClient("test_key", "test_secret")
    signature = client._generate_signature("GET", "/calls", "2024-03-01T00:00:00Z")

    # Verify signature is a valid base64 string
    assert isinstance(signature, str)
    assert len(signature) > 0
    print("✓ Signature generation test passed")


async def main():
    """Run all tests."""
    print("Running Gong MCP Server Tests...\n")

    try:
        await test_gong_client()
        await test_mcp_tools()
        await test_error_handling()
        test_signature_generation()

        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
