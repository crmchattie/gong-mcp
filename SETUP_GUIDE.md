# Gong MCP Server - Setup Guide

## Overview

This MCP server allows Claude to access your Gong sales calls and transcripts. Each user provides their own Gong API credentials, which are securely passed through HTTP Basic Authentication.

## How It Works

1. You deploy the MCP server to a remote URL (e.g., `https://gong-mcp.stag.daloopa.com`)
2. Users add the connector in Claude.ai settings
3. Users provide their **Gong Access Key** and **Gong Access Secret** as credentials
4. The server proxies requests to Gong API using the user's credentials
5. No user data or credentials are stored on the server

## Setup Instructions for Claude.ai

### Step 1: Get Your Gong API Credentials

1. Log in to your Gong account
2. Navigate to Settings > API > Create API Credentials
3. Note down your:
   - **Access Key** (e.g., `CA4ESZGLAOFX6SJWOI6HS7ZSIO6XXVGV`)
   - **Access Secret** (JWT token starting with `eyJ...`)

### Step 2: Add Connector in Claude.ai

1. Go to [claude.ai](https://claude.ai)
2. Click your profile icon → **Settings**
3. Navigate to **Connectors** section
4. Click **Add custom connector**
5. Fill in the form:
   - **Name**: `Gong Sales Intelligence`
   - **Remote MCP server URL**: `https://gong-mcp.stag.daloopa.com/server/mcp/`
   - Click **Advanced settings** ▼
   - **OAuth Client ID**: `<YOUR_GONG_ACCESS_KEY>`
   - **OAuth Client Secret**: `<YOUR_GONG_ACCESS_SECRET>`
6. Click **Add**

### Step 3: Use the Connector

In any Claude conversation:
1. The Gong connector will appear in available tools
2. Ask Claude to list your Gong calls or retrieve transcripts
3. Claude will use your credentials to access your Gong data

## Example Usage

```
You: Show me my Gong calls from this week

Claude: I'll retrieve your recent Gong calls...
[Uses list_calls tool with your credentials]

You: Can you analyze the transcript from that first call?

Claude: I'll retrieve the transcript for that call...
[Uses retrieve_transcripts tool with your credentials]
```

## Available Tools

### 1. list_calls
Lists your Gong sales calls with optional date filtering.

**Parameters:**
- `from_datetime` (optional): Start date in ISO format (e.g., `2024-03-01T00:00:00Z`)
- `to_datetime` (optional): End date in ISO format (e.g., `2024-03-31T23:59:59Z`)

**Returns:**
- Call details including ID, title, participants, duration, and timestamps

### 2. retrieve_transcripts
Retrieves detailed transcripts for specific call IDs.

**Parameters:**
- `call_ids` (required): Array of Gong call IDs

**Returns:**
- Full transcripts with speaker IDs, topics, and timestamped sentences

## Security

- ✅ Credentials are sent via HTTP Basic Auth (encrypted with HTTPS)
- ✅ Credentials are NOT stored on the server
- ✅ Each request uses the user's own Gong API credentials
- ✅ Users can only access their own Gong data
- ✅ No database or persistent storage of user information

## Troubleshooting

### Error: "Unauthorized: Missing or invalid Authorization header"
- Make sure you entered your Gong Access Key and Secret in the connector settings
- Double-check that your credentials are correct

### Error: "Gong API credentials not provided"
- The server didn't receive your credentials
- Try removing and re-adding the connector with correct credentials

### Error: "401" or "403" from Gong API
- Your Gong credentials may be invalid or expired
- Generate new API credentials in Gong settings
- Update the connector with the new credentials

## Support

For issues or questions:
- Check the [Gong API documentation](https://help.gong.io/docs/api-documentation)
- Verify your API credentials in Gong settings
- Contact your system administrator

## Technical Details

### Server Endpoints

- **Health Check**: `GET /health/` - Returns server status
- **MCP Endpoint**: `POST /server/mcp/` - MCP protocol endpoint (requires auth)

### Authentication Flow

1. Claude sends HTTP Basic Auth header: `Authorization: Basic base64(access_key:access_secret)`
2. Server extracts credentials from the header
3. Server creates a Gong API client with those credentials
4. Server makes requests to Gong API on behalf of the user
5. Server returns results to Claude

### No OAuth Required

Despite the field names "OAuth Client ID" and "OAuth Client Secret" in Claude's UI, this server does NOT use OAuth. These fields simply pass your Gong credentials via HTTP Basic Authentication. No redirect flows, no login pages, no tokens - just simple credential passing.

## Deployment

This server is already deployed at:
- **URL**: `https://gong-mcp.stag.daloopa.com/`
- **Status**: Check `/health/` endpoint

For deployment updates, see the deployment documentation or contact your DevOps team.
