"""
Chat-VRD Pipecat Bot with Cartesia Dutch TTS Support
Uses Cartesia for Dutch TTS, Gemini for everything else
"""

import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    from pipecat.frames.frames import EndFrame, TranscriptionMessage
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
    from pipecat.services.cartesia.tts import CartesiaHttpTTSService
    from pipecat.transports.services.daily import DailyParams, DailyTransport
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.processors.transcript_processor import TranscriptProcessor
    from pipecat.transcriptions.language import Language
    logger.info("✅ Pipecat modules loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Pipecat modules: {e}")
    raise

# Import model configuration
try:
    from models_config import (
        get_model_type, get_voices_for_model, 
        is_voice_supported, get_default_voice
    )
    logger.info("✅ Model configuration loaded")
except ImportError as e:
    logger.error(f"❌ Failed to import model configuration: {e}")
    raise

# Get API keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

# Cartesia Dutch voice configurations
CARTESIA_DUTCH_VOICES = {
    "male": "95856005-0332-41b0-935f-352e296aa0df",      # Dutch male voice
    "female": "79a125e8-cd45-4c13-8a67-188112f4dd22",    # Dutch female voice  
    "default": "79a125e8-cd45-4c13-8a67-188112f4dd22",  # Default to female
}

def get_system_instruction(language: str, voice_id: str = None) -> str:
    """Get appropriate system instruction based on language"""
    if language == "nl-NL":
        return """Je bent een behulpzame Nederlandse AI-assistent. 
        Spreek natuurlijk Nederlands en houd je antwoorden beknopt en vriendelijk.
        Je helpt gebruikers met hun vragen en taken."""
    elif language == "de-DE":
        return """Du bist ein hilfreicher deutscher KI-Assistent.
        Sprich natürliches Deutsch und halte deine Antworten prägnant und freundlich."""
    elif language == "fr-FR":
        return """Tu es un assistant IA français serviable.
        Parle un français naturel et garde tes réponses concises et amicales."""
    else:
        return f"""You are a helpful voice assistant. 
        Keep responses concise and natural."""


async def run_bot(
    room_url: str, 
    token: str, 
    language: str = "en-US", 
    model_id: str = "gemini-2.0-flash-exp",
    voice_id: str = None,
    ready_event: asyncio.Event = None
):
    """
    Run bot with Cartesia TTS for Dutch, Gemini TTS for other languages
    
    Args:
        room_url: Daily room URL to join
        token: Daily auth token
        language: Language code in BCP-47 format (nl-NL for Dutch)
        model_id: Gemini model ID to use
        voice_id: Voice ID (ignored for Dutch - uses Cartesia)
        ready_event: Optional event to signal when bot has joined
    """
    logger.info(f"🤖 Starting bot for room: {room_url}")
    logger.info(f"🤖 Model: {model_id}")
    logger.info(f"🌐 Language: {language}")
    
    # Check if we should use Cartesia for Dutch
    use_cartesia = (language == "nl-NL" and CARTESIA_API_KEY)
    
    if use_cartesia:
        logger.info("🇳🇱 Using Cartesia TTS for Dutch language")
    else:
        logger.info(f"🌍 Using Gemini TTS for {language}")
    
    if not GOOGLE_API_KEY:
        logger.error("❌ GOOGLE_API_KEY not configured")
        return
    
    if use_cartesia and not CARTESIA_API_KEY:
        logger.warning("⚠️ CARTESIA_API_KEY not configured, falling back to Gemini TTS")
        use_cartesia = False
    
    try:
        # Daily transport configuration
        logger.info("📡 Configuring Daily transport...")
        transport = DailyTransport(
            room_url,
            token,
            "Chat-VRD Bot",
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
            )
        )
        logger.info("✅ Daily transport configured")
        
        # Get system instruction
        system_instruction = get_system_instruction(language, voice_id)
        
        # Create pipeline based on language
        if use_cartesia:
            # DUTCH: Use Cartesia for TTS
            logger.info("🎤 Configuring Cartesia TTS for Dutch...")
            
            # Create Cartesia TTS service
            tts = CartesiaHttpTTSService(
                api_key=CARTESIA_API_KEY,
                voice_id=CARTESIA_DUTCH_VOICES.get("default"),
                model="sonic-2",
                sample_rate=16000,
                params=CartesiaHttpTTSService.InputParams(
                    language=Language.NL,
                    speed="normal"
                )
            )
            logger.info(f"✅ Cartesia TTS configured with voice: {CARTESIA_DUTCH_VOICES.get('default')}")
            
            # Configure Gemini WITHOUT TTS (only STT + LLM)
            logger.info("🧠 Configuring Gemini for STT + LLM (no TTS)...")
            # Add models/ prefix if not present (required by Gemini API)
            gemini_model = f"models/{model_id}" if not model_id.startswith("models/") else model_id
            llm = GeminiMultimodalLiveLLMService(
                api_key=GOOGLE_API_KEY,
                model=gemini_model,
                voice_id=None,  # DISABLE Gemini TTS
                system_instruction=system_instruction,
                transcribe_user_audio=True,
                transcribe_model_audio=False,  # Don't transcribe Cartesia output
            )
            logger.info("✅ Gemini configured without TTS")
            
            # Create context and aggregator
            messages = [{"role": "system", "content": system_instruction}]
            context = OpenAILLMContext(messages)
            context_aggregator = llm.create_context_aggregator(context)
            
            # Create transcript processor
            transcript = TranscriptProcessor()
            
            # Build pipeline with Cartesia TTS
            logger.info("🔧 Creating pipeline with Cartesia TTS...")
            pipeline = Pipeline([
                transport.input(),              # Daily audio input
                context_aggregator.user(),      # User context
                transcript.user(),              # Capture user transcripts
                llm,                           # Gemini (STT+LLM only)
                tts,                           # Cartesia TTS
                transport.output(),            # Daily audio output
                transcript.assistant(),        # Capture bot transcripts
                context_aggregator.assistant(), # Assistant context
            ])
            logger.info("✅ Pipeline created with Cartesia TTS")
            
        else:
            # OTHER LANGUAGES: Use Gemini for everything
            logger.info("🧠 Configuring Gemini Live with integrated TTS...")
            
            # Validate voice for the model
            model_type = get_model_type(model_id)
            available_voices = get_voices_for_model(model_id)
            
            if voice_id and not is_voice_supported(model_id, voice_id):
                logger.warning(f"⚠️ Voice {voice_id} not supported, using default")
                voice_id = get_default_voice(model_id)
            elif not voice_id:
                voice_id = get_default_voice(model_id)
            
            logger.info(f"🎤 Using Gemini voice: {voice_id}")
            
            # Configure Gemini with TTS
            # Add models/ prefix if not present (required by Gemini API)
            gemini_model = f"models/{model_id}" if not model_id.startswith("models/") else model_id
            llm = GeminiMultimodalLiveLLMService(
                api_key=GOOGLE_API_KEY,
                model=gemini_model,
                voice_id=voice_id,  # Use Gemini TTS
                system_instruction=system_instruction,
                transcribe_user_audio=True,
                transcribe_model_audio=True,
            )
            logger.info(f"✅ Gemini Live configured with voice: {voice_id}")
            
            # Create context and aggregator
            messages = [{"role": "system", "content": system_instruction}]
            context = OpenAILLMContext(messages)
            context_aggregator = llm.create_context_aggregator(context)
            
            # Create transcript processor
            transcript = TranscriptProcessor()
            
            # Build standard pipeline
            logger.info("🔧 Creating pipeline with Gemini TTS...")
            pipeline = Pipeline([
                transport.input(),              # Daily audio input
                context_aggregator.user(),      # User context
                transcript.user(),              # Capture user transcripts
                llm,                           # Gemini Live (STT+LLM+TTS)
                transport.output(),            # Daily audio output
                transcript.assistant(),        # Capture bot transcripts
                context_aggregator.assistant(), # Assistant context
            ])
            logger.info("✅ Pipeline created with Gemini TTS")
        
        # Create task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            )
        )
        logger.info("✅ Pipeline task created")
        
        # Event handlers
        @transport.event_handler("on_joined")
        async def on_joined(transport, event):
            logger.info("✅ Bot has joined the Daily room!")
            logger.info(f"🤖 Model: {model_id}")
            logger.info(f"🌐 Language: {language}")
            logger.info(f"🎤 TTS: {'Cartesia' if use_cartesia else 'Gemini'}")
            if ready_event:
                ready_event.set()
                logger.info("📡 Signaled ready_event")
        
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"👤 First participant joined: {participant['id']}")
            await task.queue_frames([context_aggregator.user().get_context_frame()])
        
        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"👋 Participant left: {participant['id']}")
            await task.queue_frame(EndFrame())
        
        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            logger.info(f"📞 Call state updated: {state}")
            if state == "left":
                await task.queue_frame(EndFrame())
        
        # Run the pipeline
        logger.info("🏃 Starting pipeline runner...")
        runner = PipelineRunner()
        await runner.run(task)
        logger.info("✅ Pipeline completed")
    
    except Exception as e:
        logger.error(f"❌ Bot error: {e}", exc_info=True)
        if ready_event:
            ready_event.set()  # Signal failure
        raise
    
    logger.info(f"🔚 Bot finished for room: {room_url}")


if __name__ == "__main__":
    """Test the bot locally"""
    if len(sys.argv) < 3:
        print("Usage: python bot_with_cartesia.py <room_url> <token> [language] [model_id]")
        sys.exit(1)
    
    room_url = sys.argv[1]
    token = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 else "en-US"
    model_id = sys.argv[4] if len(sys.argv) > 4 else "gemini-2.0-flash-exp"
    
    asyncio.run(run_bot(room_url, token, language, model_id))