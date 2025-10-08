#!/usr/bin/env python3
"""
Test which Gemini models actually work with the Live API
Even if they don't advertise bidiGenerateContent support
"""

import os
import sys

# Test models based on documentation
TEST_MODELS = [
    # Free tier models that should work according to docs
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025", 
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    
    # Paid tier models (will likely fail with free API key)
    "gemini-2.5-flash-preview-native-audio-dialog",
    "gemini-live-2.5-flash",
    "gemini-live-2.5-flash-preview-native-audio-09-2025",
]

def test_model(model_id, api_key):
    """Test if a model works with Live API by attempting to import and configure it"""
    print(f"\nTesting model: {model_id}")
    print("-" * 50)
    
    try:
        # Try importing pipecat's Gemini service
        from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
        
        # Try creating an instance with the model
        service = GeminiMultimodalLiveLLMService(
            api_key=api_key,
            model=model_id,
            voice_id="Puck",
            system_instruction="Test",
            transcribe_user_audio=True,
            transcribe_model_audio=True,
        )
        
        print(f"✅ SUCCESS: {model_id} can be configured for Live API")
        return True
        
    except ImportError as e:
        print(f"❌ ERROR: Cannot import Pipecat - {e}")
        return False
    except Exception as e:
        print(f"⚠️  FAILED: {model_id} - {str(e)}")
        return False

def main():
    # Try both API keys
    api_keys = {
        "Key 1": "AIzaSyCP2p2OhntT7UnENIWA9VbC7omZpjAQddw",
        "Key 2": "AIzaSyBgqJNUGO7MdiTavnqDbrbgY536kmBc1ug"
    }
    
    for key_name, api_key in api_keys.items():
        print(f"\n{'='*60}")
        print(f"Testing with {key_name}")
        print(f"{'='*60}")
        
        working_models = []
        failed_models = []
        
        for model in TEST_MODELS:
            if test_model(model, api_key):
                working_models.append(model)
            else:
                failed_models.append(model)
        
        print(f"\n{key_name} Summary:")
        print(f"Working models: {working_models}")
        print(f"Failed models: {failed_models}")

if __name__ == "__main__":
    main()