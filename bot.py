"""
Chat-VRD Pipecat Bot
Connects to Daily room and uses Gemini Live for conversation

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
logger.info("🚀 Initializing Pipecat bot module...")

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

# Complete list of 30 available Gemini voices from official documentation
# https://ai.google.dev/gemini-api/docs/speech-generation#voices
GEMINI_VOICES = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
    "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
    "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
    "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi",
    "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
]


def get_voice_for_language(language: str = "en-US") -> str:
    """
    Get appropriate Gemini voice ID for language
    
    Args:
        language: BCP-47 language code (e.g., "en-US", "nl-NL")
    
    Returns:
        Gemini voice ID string
    """
    # Map language codes to Gemini Live voices
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
    
    return voice_map.get(language, "Puck")  # Default to Puck


async def run_bot(room_url: str, token: str, language: str = "en-US", ready_event: asyncio.Event = None, voice_id: str = None):
    """
    Run the Pipecat bot in a Daily room
    
    Args:
        room_url: Daily room URL to join
        token: Daily auth token
        language: Language code for voice selection in BCP-47 format (e.g., "en-US", "nl-NL")
        ready_event: Optional event to signal when bot has joined the room
        voice_id: Optional specific voice ID to use (overrides language-based selection)
    """
    logger.info(f"🤖 Starting bot for room: {room_url}")
    logger.info(f"🌐 Language: {language}")
    
    if not GOOGLE_API_KEY:
        logger.error("❌ GOOGLE_API_KEY not configured")
        return
    
    logger.info("🔑 Google API key configured")
    
    try:
        # Configure voice - use provided voice_id or get language-specific voice
        if voice_id is None:
            voice_id = get_voice_for_language(language)
            logger.info(f"🎤 Auto-selected Gemini voice for {language}: {voice_id}")
        else:
            logger.info(f"🎤 Using requested Gemini voice: {voice_id}")
        
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
        
        # Configure Gemini Live service with transcription enabled
        logger.info("🧠 Configuring Gemini Live service...")
        llm = GeminiMultimodalLiveLLMService(
            api_key=GOOGLE_API_KEY,
            voice_id=voice_id,
            system_instruction="You are a helpful voice assistant. Keep responses concise and natural.",
            transcribe_user_audio=True,  # Enable user transcription
            transcribe_model_audio=True,  # Enable bot transcription
        )
        logger.info("✅ Gemini Live service configured")
        
        # Create context and aggregator (REQUIRED for Gemini Live)
        logger.info("📝 Setting up context aggregator...")
        messages = [
            {
                "role": "system",
                "content": "You are a helpful voice assistant. Keep responses concise and natural."
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
                                "text": msg.content,
                                "speaker": msg.role,  # "user" or "assistant"
                                "timestamp": msg.timestamp
                            }
                            await transport._call.sendAppMessage(message_data)
                            logger.info(f"✅ Sent transcript to frontend: [{msg.role}] {msg.content[:50]}...")
                        else:
                            logger.error("❌ Transport _call not available yet")
            except Exception as e:
                logger.error(f"❌ Error forwarding transcript: {e}", exc_info=True)
        
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
