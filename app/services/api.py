import os
import hmac
import hashlib
import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gong API Configuration
GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY")
GONG_ACCESS_SECRET = os.getenv("GONG_ACCESS_SECRET")
GONG_API_URL = "https://us-2845.api.gong.io/v2"


class GongAPIClient:
    """Gong API client for handling authentication and requests."""
    
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


class APIService:
    """API Service for Gong integration."""
    
    # Initialize Gong client if credentials are available
    _gong_client = None
    if GONG_ACCESS_KEY and GONG_ACCESS_SECRET:
        _gong_client = GongAPIClient(GONG_ACCESS_KEY, GONG_ACCESS_SECRET)

    @classmethod
    async def get_gong_calls(
        cls, 
        from_datetime: Optional[str] = None, 
        to_datetime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List Gong calls with optional date range filtering.
        
        Args:
            from_datetime: Start date/time in ISO format (e.g. 2024-03-01T00:00:00Z)
            to_datetime: End date/time in ISO format (e.g. 2024-03-31T23:59:59Z)
            
        Returns:
            Dict containing call data from Gong API
        """
        if not cls._gong_client:
            raise ValueError("Gong API credentials not configured")
            
        params = {}
        if from_datetime:
            params["fromDateTime"] = from_datetime
        if to_datetime:
            params["toDateTime"] = to_datetime

        return await cls._gong_client._request("GET", "/calls", params=params)

    @classmethod
    async def get_gong_transcripts(cls, call_ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve transcripts for specified call IDs.
        
        Args:
            call_ids: List of Gong call IDs to retrieve transcripts for
            
        Returns:
            Dict containing transcript data from Gong API
        """
        if not cls._gong_client:
            raise ValueError("Gong API credentials not configured")
            
        data = {
            "filter": {
                "callIds": call_ids,
                "includeEntities": True,
                "includeInteractionsSummary": True,
                "includeTrackers": True,
            }
        }

        return await cls._gong_client._request("POST", "/calls/transcript", data=data)