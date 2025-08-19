#!/usr/bin/env python3

import os
import hmac
import hashlib
import base64
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Redirect all logging to stderr (equivalent to JavaScript console redirection)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

# Load environment variables
load_dotenv()

# Initialize FastMCP server with proper metadata
mcp = FastMCP("gong")

# Constants
GONG_API_URL = "https://api.gong.io/v2"
GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY")
GONG_ACCESS_SECRET = os.getenv("GONG_ACCESS_SECRET")

# Check for required environment variables
if not GONG_ACCESS_KEY or not GONG_ACCESS_SECRET:
    logging.error(
        "Error: GONG_ACCESS_KEY and GONG_ACCESS_SECRET environment variables are required"
    )
    sys.exit(1)


# Type definitions
class GongCall:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.title = data.get("title")
        self.scheduled = data.get("scheduled")
        self.started = data.get("started")
        self.duration = data.get("duration")
        self.direction = data.get("direction")
        self.system = data.get("system")
        self.scope = data.get("scope")
        self.media = data.get("media")
        self.language = data.get("language")
        self.url = data.get("url")


class GongTranscript:
    def __init__(self, data: Dict[str, Any]):
        self.speaker_id = data.get("speakerId")
        self.topic = data.get("topic")
        self.sentences = data.get("sentences", [])


class GongClient:
    def __init__(self, access_key: str, access_secret: str):
        self.access_key = access_key
        self.access_secret = access_secret

    def _generate_signature(
        self, method: str, path: str, timestamp: str, params: Optional[Dict] = None
    ) -> str:
        """Generate HMAC signature for Gong API authentication."""
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

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to Gong API."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        url = f"{GONG_API_URL}{path}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Basic {base64.b64encode(f"{self.access_key}:{self.access_secret}".encode()).decode()}',
            "X-Gong-AccessKey": self.access_key,
            "X-Gong-Timestamp": timestamp,
            "X-Gong-Signature": self._generate_signature(
                method, path, timestamp, data if data is not None else params
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

    async def list_calls(
        self, from_datetime: Optional[str] = None, to_datetime: Optional[str] = None
    ) -> Dict[str, Any]:
        """List Gong calls with optional date range filtering."""
        params = {}
        if from_datetime:
            params["fromDateTime"] = from_datetime
        if to_datetime:
            params["toDateTime"] = to_datetime

        return await self._request("GET", "/calls", params=params)

    async def retrieve_transcripts(self, call_ids: List[str]) -> Dict[str, Any]:
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


# Type validation functions (equivalent to JavaScript type guards)
def is_gong_list_calls_args(args: Any) -> bool:
    """Validate arguments for list_calls tool."""
    if not isinstance(args, dict):
        return False

    # Check optional parameters
    if "fromDateTime" in args and not isinstance(args["fromDateTime"], str):
        return False
    if "toDateTime" in args and not isinstance(args["toDateTime"], str):
        return False

    return True


def is_gong_retrieve_transcripts_args(args: Any) -> bool:
    """Validate arguments for retrieve_transcripts tool."""
    if not isinstance(args, dict):
        return False

    if "callIds" not in args:
        return False

    if not isinstance(args["callIds"], list):
        return False

    # Check that all callIds are strings
    return all(isinstance(call_id, str) for call_id in args["callIds"])


# Initialize Gong client
gong_client = GongClient(GONG_ACCESS_KEY, GONG_ACCESS_SECRET)


@mcp.tool()
async def list_calls(
    from_datetime: Optional[str] = None, to_datetime: Optional[str] = None
) -> str:
    """List Gong calls with optional date range filtering. Returns call details including ID, title, start/end times, participants, and duration.
    
    IMPORTANT: When referencing any call, always note the participants and client firm information from the title. The title typically contains the client's company name and key participants. This information will be needed when analyzing transcripts later.
    
    Args:
        from_datetime: Start date/time in ISO format (e.g. 2024-03-01T00:00:00Z)
        to_datetime: End date/time in ISO format (e.g. 2024-03-31T23:59:59Z)
    """
    try:
        # Validate arguments (equivalent to JavaScript type guards)
        args = {"fromDateTime": from_datetime, "toDateTime": to_datetime}
        if not is_gong_list_calls_args(args):
            raise ValueError("Invalid arguments for list_calls")

        response = await gong_client.list_calls(from_datetime, to_datetime)
        return json.dumps(response, indent=2)
    except Exception as e:
        logging.error(f"Error in list_calls: {e}")
        return f"Error listing calls: {str(e)}"


@mcp.tool()
async def retrieve_transcripts(call_ids: List[str]) -> str:
    """Retrieve transcripts for specified call IDs. Returns detailed transcripts including speaker IDs, topics, and timestamped sentences.
    
    IMPORTANT: When analyzing any transcript, always reference the participant and client firm information from the original call listing. The call title and participant details from the list_calls tool should be used to provide context about who was involved in the conversation.
    
    Args:
        call_ids: Array of Gong call IDs to retrieve transcripts for
    """
    try:
        # Validate arguments (equivalent to JavaScript type guards)
        args = {"callIds": call_ids}
        if not is_gong_retrieve_transcripts_args(args):
            raise ValueError("Invalid arguments for retrieve_transcripts")

        response = await gong_client.retrieve_transcripts(call_ids)
        return json.dumps(response, indent=2)
    except Exception as e:
        logging.error(f"Error in retrieve_transcripts: {e}")
        return f"Error retrieving transcripts: {str(e)}"





def main():
    """Main entry point for the MCP server."""
    try:
        mcp.run(transport="stdio")
    except Exception as error:
        logging.error(f"Fatal error running server: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
