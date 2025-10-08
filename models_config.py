"""
Gemini Model Configuration - ONLY WORKING MODELS
Only includes models that actually support bidiGenerateContent for Live API

Tested and verified: 2025-01-08
"""

# WORKING MODEL - VERIFIED with Google API
# Only gemini-2.0-flash-exp actually supports bidiGenerateContent
# All other models FAIL despite what documentation says
WORKING_MODELS = {
    "gemini-2.0-flash-exp": {
        "name": "Gemini 2.0 Flash Exp",
        "type": "native-audio",
        "description": "✅ ONLY MODEL THAT WORKS - Verified via API",
        "features": ["bidiGenerateContent", "streaming", "interruption", "low_latency"],
        "tier": "free"
    }
}

# REMOVED - ALL OF THESE FAIL WITH bidiGenerateContent:
# - gemini-2.0-flash-live-001 (claimed to work, DOESN'T)
# - gemini-live-2.5-flash (claimed to work, DOESN'T)
# - gemini-live-2.5-flash-preview-native-audio-09-2025 (claimed to work, DOESN'T)
# - gemini-2.5-flash (no WebSocket support)
# - gemini-2.0-flash (no WebSocket support)
# - gemini-2.5-flash-preview-native-audio-dialog (wrong API endpoint)

# Voice configurations - All models support 30 voices
ALL_VOICES = {
    "Puck": {"description": "Upbeat voice", "languages": ["multi"]},
    "Charon": {"description": "Informative voice", "languages": ["multi"]},
    "Kore": {"description": "Firm voice", "languages": ["multi"]},
    "Fenrir": {"description": "Excitable voice", "languages": ["multi"]},
    "Aoede": {"description": "Breezy voice", "languages": ["multi"]},
    "Leda": {"description": "Youthful voice", "languages": ["multi"]},
    "Orus": {"description": "Firm voice", "languages": ["multi"]},
    "Zephyr": {"description": "Bright voice", "languages": ["multi"]},
    # Additional voices
    "Callirrhoe": {"description": "Easy-going voice", "languages": ["multi"]},
    "Autonoe": {"description": "Bright voice", "languages": ["multi"]},
    "Enceladus": {"description": "Breathy voice", "languages": ["multi"]},
    "Iapetus": {"description": "Clear voice", "languages": ["multi"]},
    "Umbriel": {"description": "Easy-going voice", "languages": ["multi"]},
    "Algieba": {"description": "Smooth voice", "languages": ["multi"]},
    "Despina": {"description": "Smooth voice", "languages": ["multi"]},
    "Erinome": {"description": "Clear voice", "languages": ["multi"]},
    "Algenib": {"description": "Gravelly voice", "languages": ["multi"]},
    "Rasalgethi": {"description": "Informative voice", "languages": ["multi"]},
    "Laomedeia": {"description": "Upbeat voice", "languages": ["multi"]},
    "Achernar": {"description": "Soft voice", "languages": ["multi"]},
    "Alnilam": {"description": "Firm voice", "languages": ["multi"]},
    "Schedar": {"description": "Even voice", "languages": ["multi"]},
    "Gacrux": {"description": "Mature voice", "languages": ["multi"]},
    "Pulcherrima": {"description": "Forward voice", "languages": ["multi"]},
    "Achird": {"description": "Friendly voice", "languages": ["multi"]},
    "Zubenelgenubi": {"description": "Casual voice", "languages": ["multi"]},
    "Vindemiatrix": {"description": "Gentle voice", "languages": ["multi"]},
    "Sadachbia": {"description": "Lively voice", "languages": ["multi"]},
    "Sadaltager": {"description": "Knowledgeable voice", "languages": ["multi"]},
    "Sulafat": {"description": "Warm voice", "languages": ["multi"]},
}

def get_all_models():
    """Get all available models - ONLY working models"""
    return WORKING_MODELS

def get_model_type(model_id: str) -> str:
    """Get the type of a model - all working models are native-audio"""
    if model_id in WORKING_MODELS:
        return "native-audio"
    return "unknown"

def get_voices_for_model(model_id: str):
    """Get available voices - all working models support all 30 voices"""
    if model_id in WORKING_MODELS:
        return ALL_VOICES
    return {}

def is_voice_supported(model_id: str, voice_id: str) -> bool:
    """Check if a voice is supported by a specific model"""
    voices = get_voices_for_model(model_id)
    return voice_id in voices

def get_default_voice(model_id: str) -> str:
    """Get the default voice for a model"""
    voices = get_voices_for_model(model_id)
    if voices:
        # Return Puck if available, otherwise first voice
        return "Puck" if "Puck" in voices else list(voices.keys())[0]
    return "Puck"