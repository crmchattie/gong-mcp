# Gong MCP Server

A Model Context Protocol (MCP) server that provides access to Gong's API for retrieving call recordings and transcripts. This server allows Claude to interact with Gong data through a standardized interface.

**Python implementation with FastMCP framework.**

## Features

- List Gong calls with optional date range filtering
- Retrieve detailed transcripts for specific calls
- Secure authentication using Gong's API credentials
- Standardized MCP interface for easy integration with Claude
- FastMCP integration with async/await support
- Full type safety with Python type hints
- **Modern Python tooling** with [uv](https://github.com/astral-sh/uv) for fast dependency management

## Prerequisites

- Python 3.10 or higher
- Gong API credentials (Access Key and Secret)

## Installation

1. Clone the repository
2. Install [uv](https://github.com/astral-sh/uv) (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```
4. Set up environment variables in `.env`:
   ```bash
   GONG_ACCESS_KEY=your_access_key_here
   GONG_ACCESS_SECRET=your_access_secret_here
   ```

## Configuring Claude

1. Open Claude Desktop settings
2. Navigate to the MCP Servers section
3. Add a new server with the following configuration:

```json
{
  "mcpServers": {
    "gong": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gong-mcp",
        "run",
        "gong_server.py"
      ]
    }
  }
}
```

4. Replace the placeholder credentials with your actual Gong API credentials from your `.env` file

## Available Tools

### List Calls

Retrieves a list of Gong calls with optional date range filtering.

**Enhanced Features:**
- **Participant Information**: Tool description emphasizes noting participants and client firm information from call titles
- **Context Preservation**: The LLM is instructed to preserve this information for use when analyzing transcripts later
- **Natural Workflow**: The LLM will naturally get participant context from list_calls before retrieving transcripts

```json
{
  name: "list_calls",
  description: "List Gong calls with optional date range filtering. Returns call details including ID, title, start/end times, participants, and duration. IMPORTANT: When referencing any call, always note the participants and client firm information from the title. The title typically contains the client's company name and key participants. This information will be needed when analyzing transcripts later.",
  inputSchema: {
    type: "object",
    properties: {
      fromDateTime: {
        type: "string",
        description: "Start date/time in ISO format (e.g. 2024-03-01T00:00:00Z)"
      },
      toDateTime: {
        type: "string",
        description: "End date/time in ISO format (e.g. 2024-03-31T23:59:59Z)"
      }
    }
  }
}
```

### Retrieve Transcripts

Retrieves detailed transcripts for specified call IDs.

**Enhanced Features:**
- **Context Awareness**: Tool description instructs the LLM to reference participant and client firm information from the original call listing
- **Cross-Reference**: The LLM is guided to use information from list_calls to provide context about who was involved
- **Natural Integration**: Works seamlessly with the list_calls workflow

```json
{
  name: "retrieve_transcripts",
  description: "Retrieve transcripts for specified call IDs. Returns detailed transcripts including speaker IDs, topics, and timestamped sentences. IMPORTANT: When analyzing any transcript, always reference the participant and client firm information from the original call listing. The call title and participant details from the list_calls tool should be used to provide context about who was involved in the conversation.",
  inputSchema: {
    type: "object",
    properties: {
      callIds: {
        type: "array",
        items: { type: "string" },
        description: "Array of Gong call IDs to retrieve transcripts for"
      }
    },
    required: ["callIds"]
  }
}
```

### Natural Workflow

The tools work together in a natural workflow:

1. **List Calls**: The LLM gets call information including titles, participants, and client firms
2. **Retrieve Transcripts**: The LLM uses the context from step 1 to provide rich analysis with participant context

This approach ensures the LLM always has the necessary context about who was involved in each conversation without requiring additional data processing.

## Usage

### Running the Server

```bash
# Run the MCP server directly
uv run gong_server.py

# Or use the installed script
uv run gong-mcp
```

### Development

```bash
# Run all tests
python3 dev.py test

# Format code
python3 dev.py format

# Lint code
python3 dev.py lint

# Start server
python3 dev.py server

# Install dependencies
python3 dev.py install

# Clean up cache files
python3 dev.py clean
```

### Manual Commands

```bash
# Run tests
uv run python test_gong_client.py

# Run with development tools
uv run black .  # Format code
uv run ruff check .  # Lint code
```

## Project Structure

```
gong-mcp/
├── gong_server.py            # Main MCP server implementation
├── pyproject.toml           # Project configuration (uv)
├── uv.lock                  # Lock file for reproducible builds
├── dev.py                   # Development script
├── test_gong_client.py      # Core functionality tests
├── test_gong_server.py      # MCP server tests
├── test_final_check.py      # Verification tests
├── example_usage.py         # Usage examples
└── COMPARISON.md            # Feature comparison
```

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 
