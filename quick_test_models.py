#!/usr/bin/env python3
import asyncio
import json
from urllib import request, error

# Test these models
MODELS_TO_TEST = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.0-flash", 
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-live-001",  # Your original model name
    "gemini-live-2.5-flash",  # Paid tier
]

API_KEY = "AIzaSyBgqJNUGO7MdiTavnqDbrbgY536kmBc1ug"

async def test_model(model_id):
    """Test if model works with Live API via WebSocket URL"""
    url = f"wss://generativelanguage.googleapis.com/v1beta/models/{model_id}:bidiGenerateContent?key={API_KEY}"
    
    try:
        # Try to create request (won't actually connect, just test URL formation)
        req = request.Request(url.replace("wss://", "https://").replace(":bidiGenerateContent", ""))
        with request.urlopen(req, timeout=2) as response:
            # If we get here, model exists
            return f"✅ {model_id}: Model exists (status {response.status})"
    except error.HTTPError as e:
        if e.code == 404:
            return f"❌ {model_id}: Model NOT FOUND"
        elif e.code == 403:
            return f"⚠️  {model_id}: Model exists but FORBIDDEN (may need paid tier)"
        else:
            return f"⚠️  {model_id}: HTTP {e.code} error"
    except Exception as e:
        return f"❌ {model_id}: Error - {str(e)[:50]}"

async def main():
    print("Testing Gemini Live API models...")
    print("=" * 60)
    
    tasks = [test_model(model) for model in MODELS_TO_TEST]
    results = await asyncio.gather(*tasks)
    
    print("\nRESULTS:")
    for result in results:
        print(result)

if __name__ == "__main__":
    asyncio.run(main())