"""
Chat-VRD Pipecat Bot with Model & Voice Selection
Connects to Daily room and uses selected Gemini model for conversation
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
logger.info("🚀 Initializing Pipecat bot module with model selection...")

try:
    from pipecat.frames.frames import EndFrame, TranscriptionMessage
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
    from pipecat.transports.daily import DailyParams, DailyTransport
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.processors.transcript_processor import TranscriptProcessor
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


async def run_bot(
    room_url: str, 
    token: str, 
    language: str = "en-US", 
    model_id: str = "gemini-2.0-flash-live-001",
    voice_id: str = None,
    ready_event: asyncio.Event = None
):
    """
    Run the Pipecat bot in a Daily room with selected model and voice
    
    Args:
        room_url: Daily room URL to join
        token: Daily auth token
        language: Language code for voice selection in BCP-47 format
        model_id: Gemini model ID to use
        voice_id: Voice ID to use (must be supported by the model)
        ready_event: Optional event to signal when bot has joined the room
    """
    logger.info(f"🤖 Starting bot for room: {room_url}")
    logger.info(f"🤖 Model: {model_id}")
    logger.info(f"🌐 Language: {language}")
    
    if not GOOGLE_API_KEY:
        logger.error("❌ GOOGLE_API_KEY not configured")
        return
    
    logger.info("🔑 Google API key configured")
    
    try:
        # Validate model and voice
        model_type = get_model_type(model_id)
        if model_type == "unknown":
            logger.error(f"❌ Unknown model: {model_id}")
            return
        
        # Get available voices for this model
        available_voices = get_voices_for_model(model_id)
        
        # Validate or select voice
        if voice_id:
            if not is_voice_supported(model_id, voice_id):
                logger.warning(f"⚠️ Voice {voice_id} not supported by model {model_id}")
                voice_id = get_default_voice(model_id)
                logger.info(f"🎤 Using default voice: {voice_id}")
            else:
                logger.info(f"🎤 Using requested voice: {voice_id}")
        else:
            voice_id = get_default_voice(model_id)
            logger.info(f"🎤 Using default voice for model: {voice_id}")
        
        logger.info(f"🤖 Model type: {model_type}, Voice: {voice_id}")
        logger.info(f"🎤 Available voices for this model: {list(available_voices.keys())}")
        
        # Daily transport configuration - minimal params
        # Gemini Live handles STT/TTS/VAD internally
        logger.info("📡 Configuring Daily transport...")
        transport = DailyTransport(
            room_url,
            token,
            "Chat-VRD Bot",
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                # Don't enable VAD/transcription - Gemini handles this
            )
        )
        logger.info("✅ Daily transport configured")
        
        # Configure Gemini Live service with selected model and voice
        logger.info(f"🧠 Configuring Gemini Live service with model: {model_id}...")
        
        # Prepare system instruction based on model type
        if model_type == "native-audio":
            system_instruction = f"""You are a helpful voice assistant using the {voice_id} voice 
            with native audio capabilities. You can express emotions naturally and provide 
            high-quality conversational responses. Keep responses concise and natural."""
        else:
            system_instruction = f"""You are a helpful voice assistant using the {voice_id} voice. 
            Keep responses concise and natural."""
        
        # Add models/ prefix if not present (required by Gemini API)
        gemini_model = f"models/{model_id}" if not model_id.startswith("models/") else model_id
        llm = GeminiMultimodalLiveLLMService(
            api_key=GOOGLE_API_KEY,
            model=gemini_model,  # Use the selected model with models/ prefix
            voice_id=voice_id,  # Use the validated voice
            system_instruction=system_instruction,
            transcribe_user_audio=True,  # Enable user transcription
            transcribe_model_audio=True,  # Enable bot transcription
        )
        logger.info(f"✅ Gemini Live service configured with {model_type} model: {model_id}")
        
        # Create context and aggregator (REQUIRED for Gemini Live)
        logger.info("📝 Setting up context aggregator...")
        messages = [
            {
                "role": "system",
                "content": system_instruction
            }
        ]
        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)
        logger.info("✅ Context aggregator configured")
        
        # Create transcript processor to capture and forward transcriptions
        logger.info("📝 Setting up transcript processor...")
        transcript = TranscriptProcessor()
        logger.info("✅ Transcript processor configured")
        
        # Create pipeline - WITH transcript processors
        logger.info("🔧 Creating pipeline...")
        pipeline = Pipeline([
            transport.input(),              # Daily audio input
            context_aggregator.user(),      # User context
            transcript.user(),              # Capture user transcripts
            llm,                            # Gemini Live (STT+LLM+TTS)
            transport.output(),             # Daily audio output
            transcript.assistant(),         # Capture bot transcripts
            context_aggregator.assistant(), # Assistant context
        ])
        logger.info("✅ Pipeline created")
        
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
            logger.info(f"🤖 Active model: {model_id} ({model_type})")
            logger.info(f"🎤 Active voice: {voice_id}")
            # Signal to /connect endpoint that bot is ready
            if ready_event:
                ready_event.set()
                logger.info("📡 Signaled ready_event - /connect can now return")
        
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"👤 First participant joined: {participant['id']}")
            # Kick off conversation
            await task.queue_frames([context_aggregator.user().get_context_frame()])
        
        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"👋 Participant left: {participant['id']} (reason: {reason})")
            await task.queue_frame(EndFrame())
        
        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            logger.info(f"📞 Call state updated: {state}")
            if state == "left":
                await task.queue_frame(EndFrame())
        
        # Register event handler to forward transcripts to frontend
        @transport.event_handler("on_transcription_message")
        async def on_transcription_message(transport, message):
            # Forward transcription to connected clients
            # This is handled by the TranscriptProcessor
            logger.debug(f"📝 Transcription: {message}")
        
        # Create runner
        logger.info("🏃 Starting pipeline runner...")
        runner = PipelineRunner()
        
        # Run the pipeline
        await runner.run(task)
        logger.info("✅ Pipeline completed")
    
    except Exception as e:
        logger.error(f"❌ Bot error: {e}", exc_info=True)
        if ready_event:
            ready_event.set()  # Signal failure so connect doesn't hang
        raise
    
    logger.info(f"🔚 Bot finished for room: {room_url}")


if __name__ == "__main__":
    """Test the bot locally (for debugging)"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python bot_with_model_selection.py <room_url> <token> [model_id] [voice_id]")
        sys.exit(1)
    
    room_url = sys.argv[1]
    token = sys.argv[2]
    model_id = sys.argv[3] if len(sys.argv) > 3 else "gemini-2.0-flash-live-001"
    voice_id = sys.argv[4] if len(sys.argv) > 4 else None
    
    asyncio.run(run_bot(room_url, token, "en-US", model_id, voice_id))