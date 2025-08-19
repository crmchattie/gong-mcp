#!/usr/bin/env python3

"""
Example usage of the GongClient without MCP framework.
This demonstrates how to use the Gong API client directly.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the GongClient from our server file
from gong_server import GongClient


async def example_list_calls():
    """Example of listing calls."""
    print("=== Example: List Calls ===")

    # Initialize client
    access_key = os.getenv("GONG_ACCESS_KEY")
    access_secret = os.getenv("GONG_ACCESS_SECRET")

    if not access_key or not access_secret:
        print("Please set GONG_ACCESS_KEY and GONG_ACCESS_SECRET in your .env file")
        return

    client = GongClient(access_key, access_secret)

    try:
        # List calls from the last 30 days
        from datetime import datetime, timedelta

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        response = await client.list_calls(
            from_datetime=start_date.isoformat() + "Z",
            to_datetime=end_date.isoformat() + "Z",
        )

        print(f"Found {len(response.get('calls', []))} calls:")
        for call in response.get("calls", [])[:5]:  # Show first 5 calls
            print(f"- {call.get('title', 'No title')} (ID: {call.get('id')})")

    except Exception as e:
        print(f"Error listing calls: {e}")


async def example_retrieve_transcripts():
    """Example of retrieving transcripts."""
    print("\n=== Example: Retrieve Transcripts ===")

    # Initialize client
    access_key = os.getenv("GONG_ACCESS_KEY")
    access_secret = os.getenv("GONG_ACCESS_SECRET")

    if not access_key or not access_secret:
        print("Please set GONG_ACCESS_KEY and GONG_ACCESS_SECRET in your .env file")
        return

    client = GongClient(access_key, access_secret)

    try:
        # First, get some call IDs
        response = await client.list_calls()
        call_ids = [
            call["id"] for call in response.get("calls", [])[:2]
        ]  # Get first 2 call IDs

        if not call_ids:
            print("No calls found to retrieve transcripts for")
            return

        # Retrieve transcripts for those calls
        transcript_response = await client.retrieve_transcripts(call_ids)

        print(
            f"Retrieved transcripts for {len(transcript_response.get('transcripts', []))} calls:"
        )
        for transcript in transcript_response.get("transcripts", []):
            speaker_id = transcript.get("speakerId", "Unknown")
            topic = transcript.get("topic", "No topic")
            sentence_count = len(transcript.get("sentences", []))
            print(
                f"- Speaker: {speaker_id}, Topic: {topic}, Sentences: {sentence_count}"
            )

    except Exception as e:
        print(f"Error retrieving transcripts: {e}")


async def main():
    """Run examples."""
    print("Gong API Client Examples\n")

    await example_list_calls()
    await example_retrieve_transcripts()

    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main())
