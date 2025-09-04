import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.api import APIService, GongAPIClient


class TestGongAPIClient:
    """Test the GongAPIClient class."""
    
    def test_init(self):
        """Test GongAPIClient initialization."""
        client = GongAPIClient("test_key", "test_secret")
        assert client.access_key == "test_key"
        assert client.access_secret == "test_secret"

    def test_generate_signature(self):
        """Test HMAC signature generation."""
        client = GongAPIClient("test_key", "test_secret")
        signature = client._generate_signature("GET", "/calls", "2024-01-01T00:00:00Z")
        assert isinstance(signature, str)
        assert len(signature) > 0

    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test successful API request."""
        client = GongAPIClient("test_key", "test_secret")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"calls": []}
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            
            result = await client._request("GET", "/calls")
            
            assert result == {"calls": []}
            mock_client.request.assert_called_once()


class TestAPIService:
    """Test the APIService class."""

    @pytest.mark.asyncio
    async def test_get_gong_calls_no_credentials(self):
        """Test get_gong_calls when credentials are not configured."""
        with patch.object(APIService, '_gong_client', None):
            with pytest.raises(ValueError, match="Gong API credentials not configured"):
                await APIService.get_gong_calls()

    @pytest.mark.asyncio
    async def test_get_gong_calls_with_dates(self):
        """Test get_gong_calls with date parameters."""
        mock_client = AsyncMock()
        mock_client._request.return_value = {"calls": [{"id": "123"}]}
        
        with patch.object(APIService, '_gong_client', mock_client):
            result = await APIService.get_gong_calls("2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z")
            
            assert result == {"calls": [{"id": "123"}]}
            mock_client._request.assert_called_once_with(
                "GET", 
                "/calls", 
                params={"fromDateTime": "2024-01-01T00:00:00Z", "toDateTime": "2024-01-31T23:59:59Z"}
            )

    @pytest.mark.asyncio
    async def test_get_gong_calls_without_dates(self):
        """Test get_gong_calls without date parameters."""
        mock_client = AsyncMock()
        mock_client._request.return_value = {"calls": []}
        
        with patch.object(APIService, '_gong_client', mock_client):
            result = await APIService.get_gong_calls()
            
            assert result == {"calls": []}
            mock_client._request.assert_called_once_with("GET", "/calls", params={})

    @pytest.mark.asyncio
    async def test_get_gong_transcripts_no_credentials(self):
        """Test get_gong_transcripts when credentials are not configured."""
        with patch.object(APIService, '_gong_client', None):
            with pytest.raises(ValueError, match="Gong API credentials not configured"):
                await APIService.get_gong_transcripts(["123"])

    @pytest.mark.asyncio
    async def test_get_gong_transcripts_success(self):
        """Test get_gong_transcripts with valid call IDs."""
        mock_client = AsyncMock()
        mock_client._request.return_value = {"transcripts": [{"callId": "123"}]}
        
        with patch.object(APIService, '_gong_client', mock_client):
            result = await APIService.get_gong_transcripts(["123", "456"])
            
            expected_data = {
                "filter": {
                    "callIds": ["123", "456"],
                    "includeEntities": True,
                    "includeInteractionsSummary": True,
                    "includeTrackers": True,
                }
            }
            
            assert result == {"transcripts": [{"callId": "123"}]}
            mock_client._request.assert_called_once_with("POST", "/calls/transcript", data=expected_data)