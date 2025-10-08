"""
Gemini Model Configuration
Defines available models and their supported voices
"""

# Half-cascade models - support only 8 voices
HALF_CASCADE_MODELS = {
    "gemini-2.0-flash-live-001": {
        "name": "Gemini 2.0 Flash Live",
        "type": "half-cascade",
        "description": "Half-cascade model with better performance for production",
        "features": ["better_tool_use", "production_ready"],
    },
    "gemini-live-2.5-flash-preview": {
        "name": "Gemini 2.5 Flash Live Preview",
        "type": "half-cascade", 
        "description": "Half-cascade preview model",
        "features": ["better_tool_use", "preview"],
    }
}

# Native audio models - support all 30 voices
NATIVE_AUDIO_MODELS = {
    "gemini-2.5-flash-native-audio-preview-09-2025": {
        "name": "Gemini 2.5 Flash Native Audio (09-2025)",
        "type": "native-audio",
        "description": "Latest native audio model with best voice quality",
        "features": ["best_quality", "emotion_aware", "thinking", "all_voices"],
    },
    "gemini-2.5-flash-preview-native-audio-dialog": {
        "name": "Gemini 2.5 Flash Native Audio Dialog",
        "type": "native-audio",
        "description": "Native audio optimized for conversations",
        "features": ["dialog_optimized", "emotion_aware", "all_voices"],
    },
    "gemini-2.5-flash-exp-native-audio-thinking-dialog": {
        "name": "Gemini 2.5 Flash Native Audio Thinking",
        "type": "native-audio",
        "description": "Experimental native audio with thinking capabilities",
        "features": ["thinking", "dialog_optimized", "experimental", "all_voices"],
    }
}

# Voice configurations
HALF_CASCADE_VOICES = {
    "Puck": {"description": "Upbeat voice", "languages": ["multi"]},
    "Charon": {"description": "Informative voice", "languages": ["multi"]},
    "Kore": {"description": "Firm voice", "languages": ["multi"]},
    "Fenrir": {"description": "Excitable voice", "languages": ["multi"]},
    "Aoede": {"description": "Breezy voice", "languages": ["multi"]},
    "Leda": {"description": "Youthful voice", "languages": ["multi"]},
    "Orus": {"description": "Firm voice", "languages": ["multi"]},
    "Zephyr": {"description": "Bright voice", "languages": ["multi"]},
}

# All 30 voices for native audio models
NATIVE_AUDIO_VOICES = {
    # Include all half-cascade voices
    **HALF_CASCADE_VOICES,
    # Additional native-only voices
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
    """Get all available models with their configurations"""
    return {**HALF_CASCADE_MODELS, **NATIVE_AUDIO_MODELS}

def get_model_type(model_id: str) -> str:
    """Get the type of a model (half-cascade or native-audio)"""
    if model_id in HALF_CASCADE_MODELS:
        return "half-cascade"
    elif model_id in NATIVE_AUDIO_MODELS:
        return "native-audio"
    return "unknown"

def get_voices_for_model(model_id: str):
    """Get available voices for a specific model"""
    model_type = get_model_type(model_id)
    if model_type == "half-cascade":
        return HALF_CASCADE_VOICES
    elif model_type == "native-audio":
        return NATIVE_AUDIO_VOICES
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