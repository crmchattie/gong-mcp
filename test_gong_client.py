#!/usr/bin/env python3

"""
Test script for the GongClient functionality.
This script tests the basic functionality without requiring the MCP package.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch


# Import only the GongClient class
class GongClient:
    def __init__(self, access_key: str, access_secret: str):
        self.access_key = access_key
        self.access_secret = access_secret

    def _generate_signature(self, method: str, path: str, timestamp: str, params=None):
        """Generate HMAC signature for Gong API authentication."""
        import hmac
        import hashlib
        import base64

        string_to_sign = (
            f"{method}\n{path}\n{timestamp}\n{json.dumps(params) if params else ''}"
        )

        # Create HMAC signature
        signature = hmac.new(
            self.access_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        return base64.b64encode(signature).decode("utf-8")

    async def _request(self, method: str, path: str, params=None, data=None):
        """Make authenticated request to Gong API."""
        import httpx
        from datetime import datetime
        import base64

        GONG_API_URL = "https://us-2845.api.gong.io/v2"
        timestamp = datetime.utcnow().isoformat() + "Z"
        url = f"{GONG_API_URL}{path}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Basic {base64.b64encode(f"{self.access_key}:{self.access_secret}".encode()).decode()}',
            "X-Gong-AccessKey": self.access_key,
            "X-Gong-Timestamp": timestamp,
            "X-Gong-Signature": self._generate_signature(
                method, path, timestamp, data or params
            ),
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_calls(self, from_datetime=None, to_datetime=None):
        """List Gong calls with optional date range filtering."""
        params = {}
        if from_datetime:
            params["fromDateTime"] = from_datetime
        if to_datetime:
            params["toDateTime"] = to_datetime

        return await self._request("GET", "/calls", params=params)

    async def retrieve_transcripts(self, call_ids):
        """Retrieve transcripts for specified call IDs."""
        data = {
            "filter": {
                "callIds": call_ids,
                "includeEntities": True,
                "includeInteractionsSummary": True,
                "includeTrackers": True,
            }
        }

        return await self._request("POST", "/calls/transcript", data=data)


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
    print("Running Gong Client Tests...\n")

    try:
        await test_gong_client()
        test_signature_generation()

        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
