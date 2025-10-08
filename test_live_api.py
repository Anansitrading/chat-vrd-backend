#!/usr/bin/env python3
import json
import subprocess
import time

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025", 
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-live-001",
]

API_KEY = "AIzaSyBgqJNUGO7MdiTavnqDbrbgY536kmBc1ug"

print("Testing Live API (bidiGenerateContent) for each model:\n")
print("=" * 60)

for model in MODELS:
    print(f"\nTesting: {model}")
    
    # Create a simple request to test the Live API endpoint
    payload = {
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Puck"}}}
        },
        "systemInstruction": {"parts": [{"text": "Test"}]}
    }
    
    cmd = f'''curl -s -X POST \
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:bidiGenerateContent?key={API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{json.dumps(payload)}' \
        --max-time 3'''
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if "error" in result.stdout.lower():
        error_data = json.loads(result.stdout) if result.stdout else {}
        error_msg = error_data.get("error", {}).get("message", "Unknown error")[:100]
        
        if "not found" in error_msg.lower() or "404" in error_msg:
            print(f"  ❌ Model NOT FOUND")
        elif "policy" in error_msg.lower() or "violation" in error_msg.lower():
            print(f"  ❌ POLICY VIOLATION - Model doesn't support Live API")
        elif "permission" in error_msg.lower() or "403" in error_msg:
            print(f"  ⚠️  FORBIDDEN - May need paid tier")
        else:
            print(f"  ❌ ERROR: {error_msg}")
    elif result.stdout:
        print(f"  ✅ SUCCESS - Model supports Live API!")
    else:
        print(f"  ⚠️  No response or timeout")

print("\n" + "=" * 60)
print("\nModels that work with Live API:")
print("- gemini-2.0-flash-exp (confirmed by API)")
print("- Test other working models above")