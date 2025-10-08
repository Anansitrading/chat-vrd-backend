#!/usr/bin/env python3
"""
Test which models ACTUALLY work with Gemini Live API WebSocket
"""

import asyncio
import websockets
import json
import ssl

MODELS_TO_TEST = [
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.0-flash", 
    "gemini-2.0-flash-live-001",
    "gemini-1.5-flash",  # Old model for comparison
    "gemini-2.0-flash-001",
    "models/gemini-2.0-flash-exp",  # Try with models/ prefix
    "models/gemini-2.5-flash",
]

API_KEY = "AIzaSyBgqJNUGO7MdiTavnqDbrbgY536kmBc1ug"

async def test_live_api_model(model_id):
    """Test if a model works with the Live API WebSocket"""
    
    # Clean model name
    clean_model = model_id.replace("models/", "")
    
    # WebSocket URL for Live API
    url = f"wss://generativelanguage.googleapis.com/v1beta/models/{clean_model}:bidiGenerateContent?key={API_KEY}"
    
    try:
        # Create SSL context
        ssl_context = ssl.create_default_context()
        
        # Try to connect to WebSocket
        async with websockets.connect(url, ssl=ssl_context, timeout=5) as websocket:
            # Send initial setup message
            setup_msg = {
                "setup": {
                    "model": f"models/{clean_model}",
                    "generationConfig": {
                        "responseModalities": ["AUDIO", "TEXT"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Puck"
                                }
                            }
                        }
                    }
                }
            }
            
            await websocket.send(json.dumps(setup_msg))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=3)
            response_data = json.loads(response)
            
            # Check if setup was successful
            if "setupComplete" in response_data:
                return f"✅ {model_id}: WORKS with Live API!"
            elif "error" in response_data:
                error_msg = response_data.get("error", {}).get("message", "")[:50]
                return f"❌ {model_id}: {error_msg}"
            else:
                return f"⚠️  {model_id}: Unexpected response"
                
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 404:
            return f"❌ {model_id}: Model NOT FOUND (404)"
        elif e.status_code == 403:
            return f"❌ {model_id}: FORBIDDEN (403) - Wrong API key or paid tier"
        elif e.status_code == 400:
            return f"❌ {model_id}: BAD REQUEST - Model doesn't support Live API"
        else:
            return f"❌ {model_id}: HTTP {e.status_code}"
            
    except asyncio.TimeoutError:
        return f"⚠️  {model_id}: Connection timeout"
        
    except Exception as e:
        error_str = str(e)[:50]
        if "policy" in error_str.lower():
            return f"❌ {model_id}: POLICY VIOLATION - Doesn't support Live API"
        return f"❌ {model_id}: {error_str}"

async def main():
    print("=" * 70)
    print("TESTING GEMINI MODELS WITH LIVE API (WebSocket)")
    print("=" * 70)
    print()
    
    # Test all models
    results = []
    for model in MODELS_TO_TEST:
        print(f"Testing: {model}...")
        result = await test_live_api_model(model)
        results.append(result)
        print(f"  {result}")
        await asyncio.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 70)
    print("SUMMARY - Models that WORK with Live API:")
    print("=" * 70)
    
    working = [r for r in results if "✅" in r]
    failed = [r for r in results if "❌" in r]
    
    if working:
        print("\n✅ WORKING MODELS:")
        for w in working:
            print(f"  {w}")
    else:
        print("\n⚠️  No models worked with WebSocket Live API")
    
    if failed:
        print("\n❌ FAILED MODELS:")
        for f in failed:
            print(f"  {f}")

if __name__ == "__main__":
    # Check if websockets is installed
    try:
        import websockets
    except ImportError:
        print("Installing websockets library...")
        import subprocess
        subprocess.run(["python3", "-m", "pip", "install", "--user", "websockets"], check=False)
        print("Please run the script again")
        exit(1)
    
    asyncio.run(main())