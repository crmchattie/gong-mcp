import json
import logging
import sys
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP, Context

from app.services.api import APIService

# Redirect all logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

# Type validation functions
def is_gong_list_calls_args(args: Any) -> bool:
    """Validate arguments for list_calls tool."""
    if not isinstance(args, dict):
        return False

    # Check optional parameters (allow None or string)
    if "fromDateTime" in args and args["fromDateTime"] is not None and not isinstance(args["fromDateTime"], str):
        return False
    if "toDateTime" in args and args["toDateTime"] is not None and not isinstance(args["toDateTime"], str):
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


# Create the MCP server
gong_mcp = FastMCP(
    name="Gong Sales Intelligence MCP",
    instructions="""
        Model Context Protocol (MCP) for retrieving sales call data from Gong's API.
        Designed for sales teams and analysts seeking insights from recorded sales conversations.
        
        CAPABILITIES:
        1. List sales calls with optional date range filtering
        2. Retrieve detailed transcripts for specific call IDs
        3. Access call metadata including participants, duration, and scheduling information
        
        WORKFLOW GUIDELINES:
        1. Call Discovery:
        - Use list_calls to find relevant sales calls
        - Filter by date range using fromDateTime and toDateTime parameters
        - Review call titles and participant information to identify relevant conversations
        
        2. Transcript Analysis:
        - Use retrieve_transcripts with specific call IDs to get detailed conversation data
        - Transcripts include speaker identification, topics, and timestamped sentences
        - Always reference participant and client information from the original call listing
        
        IMPORTANT NOTES:
        - When referencing any call, always note the participants and client firm information from the title
        - The title typically contains the client's company name and key participants
        - This information will be needed when analyzing transcripts later
        - When analyzing transcripts, always reference participant and client firm information from the original call listing
        
        DATA INTERPRETATION BEST PRACTICES:
        - Always provide context for call insights (deal stage, participant roles, key topics)
        - Highlight important conversation points, objections, and next steps
        - Consider the sales process stage when analyzing conversation content
        - Provide actionable insights rather than just raw transcript data
    """,
    debug=True,
    streamable_http_path="/mcp/",
    stateless_http=True,
)


@gong_mcp.tool()
async def list_calls(
    from_datetime: Optional[str] = None, 
    to_datetime: Optional[str] = None,
    ctx: Context = None
) -> str:
    """List Gong calls with optional date range filtering. Returns call details including ID, title, start/end times, participants, and duration.
    
    IMPORTANT: When referencing any call, always note the participants and client firm information from the title. The title typically contains the client's company name and key participants. This information will be needed when analyzing transcripts later.
    
    Args:
        from_datetime: Start date/time in ISO format (e.g. 2024-03-01T00:00:00Z)
        to_datetime: End date/time in ISO format (e.g. 2024-03-31T23:59:59Z)
    """
    # Get Gong credentials from request context
    gong_access_key = None
    gong_access_secret = None

    if ctx:
        try:
            request = ctx.get_http_request()
            # Extract credentials from request state (set by AuthenticationMiddleware)
            gong_access_key = getattr(request.state, "gong_access_key", None)
            gong_access_secret = getattr(request.state, "gong_access_secret", None)
        except Exception as e:
            logging.error(f"Error getting request context: {e}")
            # Running in stdio mode - no HTTP context available
            pass

    if not gong_access_key or not gong_access_secret:
        return "Error: Gong API credentials not provided. Please configure your Gong Access Key and Secret in the MCP connector settings."

    try:
        # Validate arguments
        args = {"fromDateTime": from_datetime, "toDateTime": to_datetime}
        if not is_gong_list_calls_args(args):
            raise ValueError("Invalid arguments for list_calls")

        # Use APIService to get calls with user's credentials
        response = await APIService.get_gong_calls(
            from_datetime,
            to_datetime,
            gong_access_key,
            gong_access_secret
        )

        return json.dumps(response, indent=2)
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error in list_calls: {e}")
        return f"Error listing calls: {str(e)}"


@gong_mcp.tool()
async def retrieve_transcripts(
    call_ids: List[str],
    ctx: Context = None
) -> str:
    """Retrieve transcripts for specified call IDs. Returns detailed transcripts including speaker IDs, topics, and timestamped sentences.
    
    IMPORTANT: When analyzing any transcript, always reference the participant and client firm information from the original call listing. The call title and participant details from the list_calls tool should be used to provide context about who was involved in the conversation.
    
    Args:
        call_ids: Array of Gong call IDs to retrieve transcripts for
    """
    # Get Gong credentials from request context
    gong_access_key = None
    gong_access_secret = None

    if ctx:
        try:
            request = ctx.get_http_request()
            # Extract credentials from request state (set by AuthenticationMiddleware)
            gong_access_key = getattr(request.state, "gong_access_key", None)
            gong_access_secret = getattr(request.state, "gong_access_secret", None)
        except Exception as e:
            logging.error(f"Error getting request context: {e}")
            # Running in stdio mode - no HTTP context available
            pass

    if not gong_access_key or not gong_access_secret:
        return "Error: Gong API credentials not provided. Please configure your Gong Access Key and Secret in the MCP connector settings."

    try:
        # Validate arguments
        args = {"callIds": call_ids}
        if not is_gong_retrieve_transcripts_args(args):
            raise ValueError("Invalid arguments for retrieve_transcripts")

        # Use APIService to get transcripts with user's credentials
        response = await APIService.get_gong_transcripts(
            call_ids,
            gong_access_key,
            gong_access_secret
        )

        return json.dumps(response, indent=2)
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error in retrieve_transcripts: {e}")
        return f"Error retrieving transcripts: {str(e)}"


if __name__ == "__main__":
    # Initialize and run the server
    gong_mcp.run(transport='stdio')