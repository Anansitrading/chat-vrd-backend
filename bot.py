"""
Chat-VRD Pipecat Bot
Connects to Daily room and uses Gemini Live for conversation
"""

import os
import sys
import asyncio
import logging

# Configure logging before other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("🚀 Initializing Pipecat bot module...")

try:
    from pipecat.frames.frames import EndFrame
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
    from pipecat.transports.daily.transport import DailyParams, DailyTransport
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    logger.info("✅ Pipecat modules loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Pipecat modules: {e}")
    raise

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
    logger.info(f"🤖 Starting bot for room: {room_url}")
    logger.info(f"🌐 Language: {language}")
    
    if not GOOGLE_API_KEY:
        logger.error("❌ GOOGLE_API_KEY not configured")
        return
    
    logger.info("🔑 Google API key configured")
    
    try:
        logger.info(f"Bot starting for room: {room_url} with language: {language}")
        
        # Configure language-specific voice
        voice_id = get_voice_for_language(language)
        logger.info(f"🎤 Selected voice: {voice_id}")
        
        # Daily transport configuration
        logger.info("📡 Configuring Daily transport...")
        transport = DailyTransport(
            room_url,
            token,
            "Chat-VRD Bot",
            DailyParams(
                api_key=os.getenv("DAILY_API_KEY"),
                audio_in_enabled=True,
                audio_out_enabled=True,
                camera_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                transcription_enabled=True,
                vad_audio_passthrough=True,
            )
        )
        logger.info("✅ Daily transport configured")
        
        # Configure Gemini Live service
        logger.info("🧠 Configuring Gemini Live service...")
        llm = GeminiMultimodalLiveLLMService(
            api_key=GOOGLE_API_KEY,
            voice_id=voice_id,
            system_instruction="You are a helpful voice assistant. Keep responses concise and natural."
        )
        logger.info("✅ Gemini Live service configured")
        
        # Create pipeline - simple STT -> LLM -> TTS
        logger.info("🔧 Creating pipeline...")
        pipeline = Pipeline([llm])
        
        # Create task
        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
        logger.info("✅ Pipeline task created")
        
        # Event handlers
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"👤 First participant joined: {participant['id']}")
            await transport.capture_participant_transcription(participant["id"])
            await task.queue_frames([llm.get_initialization_frame()])
        
        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"👋 Participant left: {participant['id']} (reason: {reason})")
            await task.queue_frame(EndFrame())
        
        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            logger.info(f"📞 Call state updated: {state}")
            if state == "left":
                await task.queue_frame(EndFrame())
        
        logger.info("🎯 Event handlers configured")
        
        # Create runner
        runner = PipelineRunner()
        
        logger.info(f"🚀 Bot joining Daily room: {room_url}")
        
        # Run the bot
        await runner.run(task)
        
        logger.info(f"✅ Bot finished for room: {room_url}")
    
    except Exception as e:
        logger.error(f"❌ Bot error in room {room_url}: {str(e)}", exc_info=True)
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
