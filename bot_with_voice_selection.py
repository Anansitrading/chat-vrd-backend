"""
Chat-VRD Pipecat Bot with Dynamic Voice Selection
Connects to Daily room and uses Gemini Live for conversation with selectable voices

Based on official Pipecat example:
https://github.com/pipecat-ai/pipecat/blob/main/examples/foundational/26b-gemini-multimodal-live-function-calling.py
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
logger.info("🚀 Initializing Pipecat bot module with voice selection...")

try:
    from pipecat.frames.frames import EndFrame, TranscriptionMessage
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
    from pipecat.transports.services.daily import DailyParams, DailyTransport
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.processors.transcript_processor import TranscriptProcessor
    logger.info("✅ Pipecat modules loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Pipecat modules: {e}")
    raise

# Get API keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Available Gemini Live voices
# Based on Google's documentation for Gemini 2.0
GEMINI_VOICES = {
    # Primary voices
    "Puck": {
        "name": "Puck",
        "description": "Natural, friendly voice",
        "languages": ["en-US", "multi"]
    },
    "Charon": {
        "name": "Charon", 
        "description": "Professional, clear voice",
        "languages": ["en-US", "en-GB", "multi"]
    },
    "Kore": {
        "name": "Kore",
        "description": "Warm, conversational voice", 
        "languages": ["en-US", "multi"]
    },
    "Fenrir": {
        "name": "Fenrir",
        "description": "Deep, authoritative voice",
        "languages": ["en-US", "multi"]
    },
    "Aoede": {
        "name": "Aoede",
        "description": "Bright, expressive voice",
        "languages": ["en-US", "multi"]
    },
    # Additional voices that may be available
    "Orbit": {
        "name": "Orbit",
        "description": "Modern, dynamic voice",
        "languages": ["en-US", "multi"]
    },
    "Perseus": {
        "name": "Perseus",
        "description": "Strong, confident voice",
        "languages": ["en-US", "multi"]
    },
    "Perse": {
        "name": "Perse",
        "description": "Gentle, soothing voice",
        "languages": ["en-US", "multi"]
    },
    "Io": {
        "name": "Io",
        "description": "Clear, articulate voice",
        "languages": ["en-US", "multi"]
    }
}


def get_voice_for_language(language: str = "en-US", preferred_voice: str = None) -> str:
    """
    Get appropriate Gemini voice ID for language with optional preference
    
    Args:
        language: BCP-47 language code (e.g., "en-US", "nl-NL")
        preferred_voice: Optional preferred voice name
    
    Returns:
        Gemini voice ID string
    """
    # If a specific voice is requested and it exists, use it
    if preferred_voice and preferred_voice in GEMINI_VOICES:
        logger.info(f"🎤 Using requested voice: {preferred_voice}")
        return preferred_voice
    
    # Map language codes to default Gemini Live voices
    # https://ai.google.dev/gemini-api/docs/models/gemini-v2
    voice_map = {
        "en-US": "Puck",  # English (US) - default
        "en-GB": "Charon",  # English (UK)
        "nl-NL": "Aoede",  # Dutch
        "es-ES": "Fenrir",  # Spanish
        "fr-FR": "Kore",  # French
        "de-DE": "Orbit",  # German
        "it-IT": "Puck",  # Italian (using default)
        "pt-BR": "Puck",  # Portuguese (using default)
    }
    
    default_voice = voice_map.get(language, "Puck")
    logger.info(f"🎤 Using default voice for {language}: {default_voice}")
    return default_voice


async def run_bot(room_url: str, token: str, language: str = "en-US", voice_id: str = None, ready_event: asyncio.Event = None):
    """
    Run the Pipecat bot in a Daily room with selectable voice
    
    Args:
        room_url: Daily room URL to join
        token: Daily auth token
        language: Language code for voice selection in BCP-47 format (e.g., "en-US", "nl-NL")
        voice_id: Optional specific voice ID to use (overrides language default)
        ready_event: Optional event to signal when bot has joined the room
    """
    logger.info(f"🤖 Starting bot for room: {room_url}")
    logger.info(f"🌐 Language: {language}")
    
    if voice_id:
        logger.info(f"🎯 Requested voice: {voice_id}")
    
    if not GOOGLE_API_KEY:
        logger.error("❌ GOOGLE_API_KEY not configured")
        return
    
    logger.info("🔑 Google API key configured")
    
    try:
        # Configure voice - either specified or language-specific
        selected_voice = get_voice_for_language(language, voice_id)
        logger.info(f"🎤 Selected Gemini voice: {selected_voice}")
        
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
        
        # Configure Gemini Live service with transcription enabled and selected voice
        logger.info(f"🧠 Configuring Gemini Live service with voice: {selected_voice}...")
        llm = GeminiMultimodalLiveLLMService(
            api_key=GOOGLE_API_KEY,
            voice_id=selected_voice,  # Use the selected voice
            system_instruction=f"You are a helpful voice assistant speaking with the {selected_voice} voice. Keep responses concise and natural.",
            transcribe_user_audio=True,  # Enable user transcription
            transcribe_model_audio=True,  # Enable bot transcription
        )
        logger.info(f"✅ Gemini Live service configured with voice: {selected_voice}")
        
        # Create context and aggregator (REQUIRED for Gemini Live)
        logger.info("📝 Setting up context aggregator...")
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful voice assistant using the {selected_voice} voice. Keep responses concise and natural."
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
            logger.info(f"✅ Bot has joined the Daily room with voice: {selected_voice}!")
            # Signal to /connect endpoint that bot is ready
            if ready_event:
                ready_event.set()
                logger.info("📡 Signaled ready_event - /connect can now return")
        
        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            logger.info(f"👤 First participant joined: {participant['id']}")
            # Kick off conversation with voice introduction
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
        # Note: Using transcript processor event handler
        @transcript.event_handler("on_transcript_update")
        async def on_transcript_update(processor, frame):
            """Forward transcript updates to Daily frontend via app messages"""
            try:
                logger.info(f"📝 Transcript update received with {len(frame.messages)} messages")
                for msg in frame.messages:
                    if isinstance(msg, TranscriptionMessage):
                        logger.info(f"📝 Transcript [{msg.role}]: {msg.content}")
                        
                        # Send to frontend via Daily app message using the internal Daily call object
                        if hasattr(transport, '_call') and transport._call:
                            message_data = {
                                "type": "transcript",
                                "speaker": msg.role,
                                "text": msg.content,
                                "timestamp": str(msg.timestamp),
                                "voice": selected_voice  # Include which voice is being used
                            }
                            
                            # Use the internal Daily call object to send app message
                            try:
                                await transport._call.sendAppMessage(message_data, "*")
                                logger.info(f"✅ Sent transcript to frontend: {msg.role}: {msg.content[:50]}...")
                            except AttributeError:
                                logger.warning("⚠️ Daily call object doesn't have sendAppMessage method")
                            except Exception as e:
                                logger.error(f"❌ Failed to send transcript: {e}")
                        else:
                            logger.warning("⚠️ Transport doesn't have Daily call object")
            except Exception as e:
                logger.error(f"❌ Error in transcript handler: {e}")
        
        # Run the pipeline
        logger.info(f"🚀 Starting pipeline with voice {selected_voice}...")
        runner = PipelineRunner()
        await runner.run(task)
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        raise
    finally:
        logger.info("🛑 Bot stopped")


# Export the available voices for the API
def get_available_voices():
    """Get list of available Gemini voices"""
    return list(GEMINI_VOICES.keys())


def get_voice_info(voice_id: str):
    """Get information about a specific voice"""
    return GEMINI_VOICES.get(voice_id, None)