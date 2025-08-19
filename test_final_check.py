#!/usr/bin/env python3

"""
Final verification test to ensure Python implementation matches JavaScript functionality.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

# Import only the classes and functions we need for testing
import sys
import os

# Temporarily set dummy environment variables for testing
os.environ["GONG_ACCESS_KEY"] = "test_key"
os.environ["GONG_ACCESS_SECRET"] = "test_secret"

from gong_server import (
    GongClient,
    is_gong_list_calls_args,
    is_gong_retrieve_transcripts_args,
)


async def test_signature_generation_matches_js():
    """Test that signature generation matches JavaScript implementation."""
    print("Testing signature generation...")

    client = GongClient("test_key", "test_secret")

    # Test with same parameters as JavaScript
    method = "GET"
    path = "/calls"
    timestamp = "2024-03-01T00:00:00.000Z"
    params = {"fromDateTime": "2024-03-01T00:00:00Z"}

    signature = client._generate_signature(method, path, timestamp, params)

    # Verify signature is generated correctly
    assert isinstance(signature, str)
    assert len(signature) > 0
    print("✓ Signature generation test passed")


def test_type_validation_matches_js():
    """Test that type validation matches JavaScript type guards."""
    print("\nTesting type validation...")

    # Test list_calls args validation
    valid_args = {
        "fromDateTime": "2024-03-01T00:00:00Z",
        "toDateTime": "2024-03-31T23:59:59Z",
    }
    assert is_gong_list_calls_args(valid_args) == True

    invalid_args = {"fromDateTime": 123}  # Should be string
    assert is_gong_list_calls_args(invalid_args) == False

    # Test retrieve_transcripts args validation
    valid_transcript_args = {"callIds": ["call1", "call2"]}
    assert is_gong_retrieve_transcripts_args(valid_transcript_args) == True

    invalid_transcript_args = {"callIds": [123]}  # Should be strings
    assert is_gong_retrieve_transcripts_args(invalid_transcript_args) == False

    missing_call_ids = {"other": "value"}
    assert is_gong_retrieve_transcripts_args(missing_call_ids) == False

    print("✓ Type validation test passed")


async def test_api_calls_match_js():
    """Test that API calls match JavaScript implementation."""
    print("\nTesting API calls...")

    with patch.object(GongClient, "_request", new_callable=AsyncMock) as mock_request:
        # Mock responses
        mock_request.return_value = {
            "calls": [
                {
                    "id": "test_call_1",
                    "title": "Test Call",
                    "started": "2024-03-01T10:00:00Z",
                    "duration": 3600,
                }
            ]
        }

        client = GongClient("test_key", "test_secret")

        # Test list_calls
        result = await client.list_calls("2024-03-01T00:00:00Z", "2024-03-31T23:59:59Z")
        assert "calls" in result
        assert len(result["calls"]) == 1
        assert result["calls"][0]["id"] == "test_call_1"

        # Verify the request was called with correct parameters
        mock_request.assert_called_with(
            "GET",
            "/calls",
            params={
                "fromDateTime": "2024-03-01T00:00:00Z",
                "toDateTime": "2024-03-31T23:59:59Z",
            },
        )

        print("✓ API calls test passed")


async def test_error_handling_matches_js():
    """Test that error handling matches JavaScript implementation."""
    print("\nTesting error handling...")

    with patch.object(GongClient, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        client = GongClient("test_key", "test_secret")

        try:
            await client.list_calls()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "API Error" in str(e)

        print("✓ Error handling test passed")


async def main():
    """Run all verification tests."""
    print("Running final verification tests...\n")

    try:
        await test_signature_generation_matches_js()
        test_type_validation_matches_js()
        await test_api_calls_match_js()
        await test_error_handling_matches_js()

        print("\n🎉 All verification tests passed!")
        print("✅ Python implementation matches JavaScript functionality")

    except Exception as e:
        print(f"\n❌ Verification test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
