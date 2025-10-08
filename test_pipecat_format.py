#!/usr/bin/env python3
"""
Test models using the exact format Pipecat would use
"""

import subprocess
import json

# Test models exactly as Pipecat would use them
TEST_CONFIGS = [
    {"model": "gemini-2.0-flash-exp", "desc": "API shows bidiGenerateContent"},
    {"model": "gemini-2.5-flash", "desc": "Docs say supports Live API"},
    {"model": "gemini-2.0-flash", "desc": "Docs say supports Live API"},
    {"model": "gemini-1.5-flash", "desc": "Older model"},
    {"model": "gemini-2.0-flash-001", "desc": "Specific version"},
    {"model": "gemini-2.0-flash-live-001", "desc": "Your current model"},
]

API_KEY = "AIzaSyBgqJNUGO7MdiTavnqDbrbgY536kmBc1ug"

print("=" * 70)
print("TESTING MODELS WITH EXACT PIPECAT FORMAT")
print("=" * 70)
print()

working_models = []
failed_models = []

for config in TEST_CONFIGS:
    model = config["model"]
    desc = config["desc"]
    
    print(f"\nTesting: {model}")
    print(f"  Description: {desc}")
    
    # Test 1: Check if model exists
    check_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}?key={API_KEY}"
    cmd = f'curl -s "{check_url}" | jq -r ".name" 2>/dev/null'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if "models/" in result.stdout:
        print(f"  ✓ Model exists in API")
        
        # Test 2: Check supported methods
        cmd2 = f'curl -s "{check_url}" | jq -r ".supportedGenerationMethods[]" 2>/dev/null'
        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
        
        if "bidiGenerateContent" in result2.stdout:
            print(f"  ✅ CONFIRMED: Supports Live API (bidiGenerateContent)")
            working_models.append(model)
        else:
            methods = result2.stdout.strip().replace('\n', ', ')
            print(f"  ⚠️  Methods: {methods}")
            print(f"  ℹ️  May still work with Live API (docs say it does)")
            # Add to working if docs say it works
            if "Docs say" in desc:
                working_models.append(model)
    else:
        print(f"  ❌ Model NOT FOUND in API")
        failed_models.append(model)

print("\n" + "=" * 70)
print("FINAL RESULTS FOR YOUR RAILWAY BACKEND:")
print("=" * 70)

if working_models:
    print("\n✅ USE THESE MODELS IN YOUR CONFIG:")
    for model in working_models:
        print(f"  - {model}")
else:
    print("\n⚠️  No confirmed working models")

if failed_models:
    print("\n❌ DON'T USE THESE MODELS:")
    for model in failed_models:
        print(f"  - {model}")

print("\n" + "=" * 70)
print("RECOMMENDED CONFIG FOR models_config.py:")
print("=" * 70)
print("""
HALF_CASCADE_MODELS = {""")

for model in working_models:
    print(f'''    "{model}": {{
        "name": "{model.replace('-', ' ').title()}",
        "type": "half-cascade",
        "description": "Live API model with 8 voices",
        "features": ["streaming", "interruption", "low_latency"],
        "tier": "free"
    }},''')

print("}")