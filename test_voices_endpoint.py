#!/usr/bin/env python3
"""Test script to verify the /voices endpoint"""

import requests
import json

BACKEND_URL = "https://chat-vrd-backend-production.up.railway.app"

def test_voices_endpoint():
    print("Testing /voices endpoint...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/voices")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /voices endpoint returned {response.status_code}")
            print(f"\nDefault voice: {data.get('default', 'Not specified')}")
            print(f"\nAvailable voices ({len(data.get('voices', []))}):")
            
            for voice in data.get('voices', []):
                print(f"  • {voice['id']}: {voice['description']}")
                
        else:
            print(f"❌ /voices endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing /voices endpoint: {e}")

if __name__ == "__main__":
    test_voices_endpoint()