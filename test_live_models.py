import json

# Based on documentation, these models should support Live API
LIVE_API_MODELS = {
    # Free tier models with Live API
    "gemini-2.5-flash": {
        "tier": "free",
        "display_name": "Gemini 2.5 Flash",
        "description": "Fast model with Live API support",
        "voices": 8  # Half-cascade voices
    },
    "gemini-2.5-flash-preview-09-2025": {
        "tier": "free",
        "display_name": "Gemini 2.5 Flash Preview",
        "description": "Preview model with Live API support",
        "voices": 8  # Half-cascade voices
    },
    "gemini-2.0-flash": {
        "tier": "free",
        "display_name": "Gemini 2.0 Flash",
        "description": "Previous generation with Live API support",
        "voices": 8  # Half-cascade voices
    },
    "gemini-2.0-flash-exp": {
        "tier": "free",
        "display_name": "Gemini 2.0 Flash Experimental",
        "description": "Experimental model with Live API",
        "voices": 8  # Half-cascade voices
    },
    
    # Paid tier native audio models
    "gemini-2.5-flash-preview-native-audio-dialog": {
        "tier": "paid",
        "display_name": "Gemini 2.5 Flash Native Audio Dialog",
        "description": "Native audio with emotion-aware responses",
        "voices": 30  # All voices including native audio
    },
    "gemini-live-2.5-flash": {
        "tier": "paid_ga",  # Private GA - requires approval
        "display_name": "Gemini Live 2.5 Flash",
        "description": "Production native audio model",
        "voices": 30
    },
    "gemini-live-2.5-flash-preview-native-audio-09-2025": {
        "tier": "paid",
        "display_name": "Gemini Live 2.5 Flash Native Audio Preview",
        "description": "Public preview of native audio capabilities",
        "voices": 30
    }
}

print("Models that should work with Live API (according to docs):")
print("=" * 60)
for model_id, info in LIVE_API_MODELS.items():
    print(f"\n{model_id}:")
    print(f"  Tier: {info['tier']}")
    print(f"  Display: {info['display_name']}")
    print(f"  Voices: {info['voices']}")
    print(f"  Description: {info['description']}")
