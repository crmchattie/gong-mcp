#!/usr/bin/env python3
"""
Direct test of MCP tools without OAuth authentication
"""
import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('production.env')

# Import the MCP tools directly
from app.gong_mcp import gong_mcp

async def test_mcp_tools_direct():
    """Test MCP tools directly without authentication"""
    print("🧪 Testing Gong MCP Tools Directly...")
    
    # Test 1: List calls
    print("\n1️⃣ Testing list_calls...")
    try:
        result = await gong_mcp.tools["list_calls"].func(
            from_datetime="2024-01-01T00:00:00Z",
            to_datetime="2024-12-31T23:59:59Z"
        )
        calls_data = json.loads(result)
        print(f"✅ list_calls successful!")
        print(f"   Found {calls_data.get('records', {}).get('totalRecords', 0)} total calls")
        print(f"   Retrieved {len(calls_data.get('calls', []))} calls in this page")
        
        # Show first few call titles
        calls = calls_data.get('calls', [])[:3]
        for i, call in enumerate(calls, 1):
            print(f"   {i}. {call.get('title', 'No title')} (ID: {call.get('id', 'No ID')})")
            
        return calls_data.get('calls', [])
            
    except Exception as e:
        print(f"❌ list_calls failed: {e}")
        return []
    
    # Test 2: Retrieve transcripts
    print("\n2️⃣ Testing retrieve_transcripts...")
    try:
        # Use the first call ID from the previous result
        if calls_data.get('calls'):
            call_id = calls_data['calls'][0]['id']
            print(f"   Using call ID: {call_id}")
            
            result = await retrieve_transcripts([call_id])
            transcript_data = json.loads(result)
            print(f"✅ retrieve_transcripts successful!")
            print(f"   Retrieved transcript for call: {call_id}")
            
            # Show transcript summary
            call_transcripts = transcript_data.get('callTranscripts', [])
            if call_transcripts:
                transcript = call_transcripts[0]
                sentences = transcript.get('sentences', [])
                print(f"   Transcript has {len(sentences)} sentences")
                if sentences:
                    print(f"   First sentence: {sentences[0].get('text', 'No text')[:100]}...")
            else:
                print("   No transcript data found")
        else:
            print("❌ No calls available to test transcript retrieval")
            
    except Exception as e:
        print(f"❌ retrieve_transcripts failed: {e}")
    
    print("\n🎉 MCP Tools testing completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools_direct())
