# Gong MCP Server Testing Guide

## Quick Start with MCP Inspector

### 1. Launch Inspector
```bash
npx @modelcontextprotocol/inspector
```
Opens at: http://localhost:6274

### 2. Connect Server
- **Transport**: `stdio`
- **Command**: `uv run python /Users/corymchattie/Projects/gong-mcp/run_mcp_server.py`
- **Directory**: `/Users/corymchattie/Projects/gong-mcp`

### 3. Test Tools

#### list_calls
```json
{
  "from_datetime": "2024-01-01T00:00:00Z",
  "to_datetime": "2024-12-31T23:59:59Z"
}
```

#### retrieve_transcripts
```json
{
  "call_ids": ["call-id-from-list-result"]
}
```

## Expected Results

### list_calls Response
```json
{
  "calls": [
    {
      "id": "call-id",
      "title": "Client Meeting - Company Name",
      "started": "2024-01-15T10:00:00Z",
      "ended": "2024-01-15T11:00:00Z",
      "participants": [...]
    }
  ],
  "records": {
    "totalRecords": 100,
    "currentPageSize": 50
  }
}
```

### retrieve_transcripts Response
```json
{
  "callTranscripts": [
    {
      "callId": "call-id",
      "sentences": [
        {
          "speakerId": "speaker-1",
          "text": "Hello, thanks for joining...",
          "start": 1000,
          "end": 3000
        }
      ],
      "topics": [...],
      "participants": [...]
    }
  ]
}
```

## Troubleshooting

### Common Issues
1. **"Gong API credentials not configured"**
   - Check `production.env` has valid `GONG_ACCESS_KEY` and `GONG_ACCESS_SECRET`

2. **Server won't connect**
   - Ensure you're in the correct directory
   - Check that `uv` is installed and working

3. **Empty responses**
   - Verify API credentials are valid
   - Check date ranges are reasonable
   - Ensure you have access to Gong data

### Test Commands
```bash
# Test server directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}' | uv run python run_mcp_server.py

# Run direct test
uv run python test_mcp_direct.py
```

## Environment Setup
Make sure your `production.env` contains:
```env
GONG_ACCESS_KEY=your_access_key
GONG_ACCESS_SECRET=your_access_secret
```
