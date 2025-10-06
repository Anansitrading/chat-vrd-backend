"""
Chat-VRD Pipecat Bot
Connects to Daily room and uses Gemini Live for conversation
"""

import os
import sys
import asyncio
import logging

from pipecat.frames.frames import EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer

from loguru import logger as loguru_logger

# Configure logging
logger = logging.getLogger(__name__)

# Get API keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


async def run_bot(room_url: str, token: str, language: str = "en-US"):
    """
    Run the Pipecat bot in a Daily room
    
    Args:
        room_url: Daily room URL to join
        token: Daily auth token
        language: Language code for STT/TTS in BCP-47 format (e.g., "en-US", "nl-NL")
    """
    
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY not configured")
        return
    
    try:
        logger.info(f"Bot starting for room: {room_url} with language: {language}")
        
        # Daily transport configuration
        transport = DailyTransport(
            room_url,
            token,
            "Pipecat Bot",
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                camera_out_enabled=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,  # Use Daily's built-in transcription
            )
        )
        
        # Configure Gemini Live with detected language from Deepgram
        # This ensures proper STT/TTS in the user's language
        llm = GeminiMultimodalLiveLLMService(
            api_key=GOOGLE_API_KEY,
            voice_id="Puck",  # Gemini voice
            # Configure speech with detected language
            speech_config={
                "language_code": language,  # BCP-47 code from Deepgram detection
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Puck"
                    }
                }
            },
            # Enable input/output transcription for proper language handling
            input_audio_transcription={},
            output_audio_transcription={},
        )
        
        # Simple pipeline: Gemini Live handles everything
        pipeline = Pipeline([
            transport.input(),
            llm,  # Handles STT, LLM, TTS, and language detection
            transport.output(),
        ])
        
        # Create task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )
        
        # Create runner
        runner = PipelineRunner()
        
        logger.info(f"Bot joining Daily room: {room_url}")
        
        # Run the bot
        await runner.run(task)
        
        logger.info(f"Bot finished for room: {room_url}")
    
    except Exception as e:
        logger.error(f"Bot error in room {room_url}: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # For testing locally
    room_url = os.getenv("DAILY_ROOM_URL")
    token = os.getenv("DAILY_TOKEN")
    language = os.getenv("LANGUAGE", "en-US")
    
    if not room_url or not token:
        print("Usage: DAILY_ROOM_URL=<url> DAILY_TOKEN=<token> python bot.py")
        sys.exit(1)
    
    asyncio.run(run_bot(room_url, token, language))
