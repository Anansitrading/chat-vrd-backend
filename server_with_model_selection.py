"""
Chat-VRD Pipecat Backend Server with Model & Voice Selection
FastAPI server that creates Daily rooms and spawns Pipecat bots with selectable models and voices
"""

import os
import asyncio
import aiohttp
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import model configuration
try:
    from models_config import (
        get_all_models, get_model_type, get_voices_for_model,
        is_voice_supported, get_default_voice
    )
    MODELS_AVAILABLE = True
    logger.info("✅ Model configuration loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Model configuration failed to import: {e}")
    MODELS_AVAILABLE = False

# Import bot modules
try:
    from bot_with_model_selection import run_bot as run_bot_standard
    BOT_AVAILABLE = True
    logger.info("✅ Standard bot module loaded")
    
    # Try to import Cartesia bot
    try:
        from bot_with_cartesia import run_bot as run_bot_cartesia
        CARTESIA_AVAILABLE = True
        logger.info("✅ Cartesia bot module loaded")
    except Exception as e:
        CARTESIA_AVAILABLE = False
        run_bot_cartesia = None
        logger.warning(f"⚠️ Cartesia bot not available: {e}")
        
except Exception as e:
    logger.warning(f"⚠️  Bot modules failed to import: {e}")
    logger.warning("⚠️  Server will start but /connect endpoint will be unavailable")
    BOT_AVAILABLE = False
    CARTESIA_AVAILABLE = False
    run_bot_standard = None
    run_bot_cartesia = None

# Initialize FastAPI
app = FastAPI(title="Chat-VRD Pipecat Backend with Model & Voice Selection")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DAILY_API_KEY = os.getenv("DAILY_API_KEY")
DAILY_API_URL = "https://api.daily.co/v1"

# Log environment status on startup
logger.info(f"🔧 Daily API configured: {bool(DAILY_API_KEY)}")
logger.info(f"🔧 Google API configured: {bool(os.getenv('GOOGLE_API_KEY'))}")
logger.info(f"🔧 Bot module available: {BOT_AVAILABLE}")
logger.info(f"🔧 Model configuration available: {MODELS_AVAILABLE}")

# Track active bots and their ready events
active_bots = {}
bot_ready_events = {}


class ConnectRequest(BaseModel):
    model_id: Optional[str] = "gemini-2.0-flash-live-001"  # Default to half-cascade
    voice_id: Optional[str] = None  # Will use default for model if not specified
    language: Optional[str] = "en-US"


class ModelInfo(BaseModel):
    id: str
    name: str
    type: str  # "half-cascade" or "native-audio"
    description: str
    features: List[str]
    voice_count: int
    voices: Dict[str, Dict]  # Voice ID -> info


class VoiceInfo(BaseModel):
    id: str
    description: str
    languages: List[str]


@app.on_event("startup")
async def startup_event():
    """Run startup checks and logging"""
    logger.info("🚀 Starting Chat-VRD Pipecat Backend with Model & Voice Selection...")
    
    # CRITICAL: Log the PORT environment variable for debugging
    port = os.getenv('PORT')
    logger.info(f"🔧 PORT environment variable: {port}")
    if not port:
        logger.warning("⚠️  WARNING: PORT environment variable is NOT SET!")
        logger.warning("⚠️  Railway requires $PORT to be set for routing")
    
    # Check required environment variables
    required_vars = ["DAILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {missing_vars}")
    else:
        logger.info("✅ All required environment variables configured")
    
    # Check optional variables
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("⚠️  GOOGLE_API_KEY not set - bot functionality will be limited")
    
    # Log available models
    if MODELS_AVAILABLE:
        models = get_all_models()
        logger.info(f"🤖 Available models: {list(models.keys())}")
    
    logger.info("✅ Startup complete - ready to accept connections")


async def create_daily_room(language: str = "en-US") -> tuple[str, str, str]:
    """Create a Daily.co room and return room_url, bot_token, client_token"""
    
    if not DAILY_API_KEY:
        raise HTTPException(500, "DAILY_API_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Create room with privacy settings
    room_config = {
        "properties": {
            "exp": int(time.time()) + 3600,  # 1 hour from now (Unix timestamp)
            "enable_chat": True,
            "enable_screenshare": False,
            "start_video_off": True,
            "start_audio_off": False,
        }
    }
    
    async with aiohttp.ClientSession() as session:
        # Create room
        async with session.post(
            f"{DAILY_API_URL}/rooms",
            headers=headers,
            json=room_config
        ) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Failed to create room: {text}")
                raise HTTPException(500, f"Failed to create Daily room: {text}")
            
            data = await response.json()
            room_name = data["name"]
            room_url = data["url"]
            logger.info(f"Created Daily room: {room_url}")
        
        # Create bot token (owner privileges)
        bot_token_config = {
            "properties": {
                "room_name": room_name,
                "is_owner": True,
            }
        }
        
        async with session.post(
            f"{DAILY_API_URL}/meeting-tokens",
            headers=headers,
            json=bot_token_config
        ) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Failed to create bot token: {text}")
                raise HTTPException(500, f"Failed to create bot token: {text}")
            
            data = await response.json()
            bot_token = data["token"]
        
        # Create client token
        client_token_config = {
            "properties": {
                "room_name": room_name,
            }
        }
        
        async with session.post(
            f"{DAILY_API_URL}/meeting-tokens",
            headers=headers,
            json=client_token_config
        ) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Failed to create client token: {text}")
                raise HTTPException(500, f"Failed to create client token: {text}")
            
            data = await response.json()
            client_token = data["token"]
    
    return room_url, bot_token, client_token


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "pipecat-gemini-bot-with-model-selection",
        "version": "2.1.0",
        "daily_api_configured": bool(DAILY_API_KEY),
        "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "cartesia_api_configured": bool(os.getenv("CARTESIA_API_KEY")),
        "bot_available": BOT_AVAILABLE,
        "cartesia_bot_available": CARTESIA_AVAILABLE,
        "models_available": MODELS_AVAILABLE
    }


@app.get("/debug/gemini-models")
async def debug_gemini_models():
    """Check what models are actually available from Google's API with our key"""
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        raise HTTPException(500, "GOOGLE_API_KEY not configured")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={google_key}"
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    return {"error": text, "status": response.status}
                
                data = await response.json()
                
                # Filter to only models that support bidiGenerateContent
                live_models = []
                for model in data.get("models", []):
                    methods = model.get("supportedGenerationMethods", [])
                    if "bidiGenerateContent" in methods:
                        live_models.append({
                            "name": model["name"],
                            "displayName": model.get("displayName", ""),
                            "supportedGenerationMethods": methods
                        })
                
                return {
                    "total_models": len(data.get("models", [])),
                    "live_api_models": live_models,
                    "live_api_count": len(live_models)
                }
    except Exception as e:
        return {"error": str(e)}


@app.get("/models")
async def list_models():
    """Get list of available models with their voice configurations"""
    if not MODELS_AVAILABLE:
        raise HTTPException(503, "Model configuration not available")
    
    models = []
    all_models = get_all_models()
    
    for model_id, info in all_models.items():
        voices = get_voices_for_model(model_id)
        model_info = ModelInfo(
            id=model_id,
            name=info["name"],
            type=info["type"],
            description=info["description"],
            features=info["features"],
            voice_count=len(voices),
            voices=voices
        )
        models.append(model_info)
    
    return {
        "models": models,
        "default_model": "gemini-2.0-flash-live-001"
    }


@app.get("/models/{model_id}")
async def get_model_details(model_id: str):
    """Get details about a specific model including its voices"""
    if not MODELS_AVAILABLE:
        raise HTTPException(503, "Model configuration not available")
    
    all_models = get_all_models()
    if model_id not in all_models:
        raise HTTPException(404, f"Model '{model_id}' not found")
    
    info = all_models[model_id]
    voices = get_voices_for_model(model_id)
    
    return ModelInfo(
        id=model_id,
        name=info["name"],
        type=info["type"],
        description=info["description"],
        features=info["features"],
        voice_count=len(voices),
        voices=voices
    )


@app.get("/models/{model_id}/voices")
async def get_model_voices(model_id: str):
    """Get available voices for a specific model"""
    if not MODELS_AVAILABLE:
        raise HTTPException(503, "Model configuration not available")
    
    voices = get_voices_for_model(model_id)
    if not voices:
        raise HTTPException(404, f"Model '{model_id}' not found or has no voices")
    
    voice_list = []
    for voice_id, info in voices.items():
        voice_list.append(VoiceInfo(
            id=voice_id,
            description=info["description"],
            languages=info["languages"]
        ))
    
    return {
        "model_id": model_id,
        "model_type": get_model_type(model_id),
        "voices": voice_list,
        "default_voice": get_default_voice(model_id)
    }


@app.post("/connect")
async def connect(request: ConnectRequest):
    """
    Create a Daily room and spawn a Pipecat bot with selected model and voice
    
    This endpoint:
    1. Creates a Daily.co room
    2. Validates model and voice selection
    3. Spawns a Pipecat bot with the selected configuration
    4. Returns room URL and client token
    """
    
    # Check if bot module is available
    if not BOT_AVAILABLE:
        raise HTTPException(503, "Bot module not available - check server logs")
    
    if not MODELS_AVAILABLE:
        raise HTTPException(503, "Model configuration not available")
    
    # Validate model
    all_models = get_all_models()
    if request.model_id not in all_models:
        available = list(all_models.keys())
        raise HTTPException(
            400, 
            f"Invalid model_id '{request.model_id}'. Available models: {available}"
        )
    
    # Validate voice if specified
    if request.voice_id:
        if not is_voice_supported(request.model_id, request.voice_id):
            available_voices = list(get_voices_for_model(request.model_id).keys())
            raise HTTPException(
                400,
                f"Voice '{request.voice_id}' not supported by model '{request.model_id}'. Available voices: {available_voices}"
            )
    else:
        # Use default voice for the model
        request.voice_id = get_default_voice(request.model_id)
    
    logger.info(f"🤖 Model: {request.model_id}, Voice: {request.voice_id}, Language: {request.language}")
    
    try:
        # Create Daily room
        logger.info(f"📞 Creating Daily room...")
        room_url, bot_token, client_token = await create_daily_room(request.language)
        logger.info(f"✅ Daily room created: {room_url}")
        
        # Create event for bot readiness
        ready_event = asyncio.Event()
        bot_ready_events[room_url] = ready_event
        
        # Choose bot based on language
        use_cartesia = (request.language == "nl-NL" and 
                       os.getenv("CARTESIA_API_KEY") and 
                       CARTESIA_AVAILABLE)
        
        if use_cartesia:
            logger.info("🇳🇱 Using Cartesia bot for Dutch TTS")
            run_bot = run_bot_cartesia
        else:
            logger.info("🌍 Using standard Gemini bot")
            run_bot = run_bot_standard
        
        # Spawn bot task with selected model and voice
        bot_task = asyncio.create_task(
            run_bot(
                room_url, 
                bot_token, 
                request.language,
                request.model_id,
                request.voice_id,
                ready_event
            )
        )
        active_bots[room_url] = bot_task
        logger.info(f"🤖 Bot task spawned with model: {request.model_id}, voice: {request.voice_id}")
        
        # Wait for bot to join (with timeout)
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=10.0)
            logger.info(f"✅ Bot successfully joined room: {room_url}")
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Bot joining timeout for room: {room_url}")
            # Continue anyway - bot might still join
        
        # Clean up event
        del bot_ready_events[room_url]
        
        # Get model and voice info
        model_info = all_models[request.model_id]
        voice_info = get_voices_for_model(request.model_id).get(request.voice_id, {})
        
        return {
            "room_url": room_url,
            "token": client_token,
            "language": request.language,
            "model": {
                "id": request.model_id,
                "name": model_info["name"],
                "type": model_info["type"]
            },
            "voice": {
                "id": request.voice_id,
                "description": voice_info.get("description", "Unknown")
            },
            "bot_status": "joined" if ready_event.is_set() else "joining"
        }
    
    except Exception as e:
        logger.error(f"❌ Error in /connect: {e}")
        raise HTTPException(500, f"Failed to create room or spawn bot: {str(e)}")


@app.post("/disconnect/{room_name}")
async def disconnect(room_name: str):
    """Disconnect bot from a specific room"""
    
    # Find room URL from room name
    room_url = None
    for url in active_bots.keys():
        if room_name in url:
            room_url = url
            break
    
    if not room_url:
        raise HTTPException(404, f"No active bot found for room: {room_name}")
    
    try:
        # Cancel bot task
        if room_url in active_bots:
            bot_task = active_bots[room_url]
            bot_task.cancel()
            del active_bots[room_url]
            logger.info(f"🛑 Cancelled bot task for room: {room_url}")
        
        return {"status": "disconnected", "room": room_name}
    
    except Exception as e:
        logger.error(f"❌ Error disconnecting bot: {e}")
        raise HTTPException(500, f"Failed to disconnect bot: {str(e)}")


@app.get("/active")
async def list_active_bots():
    """List all active bot sessions"""
    active = []
    for room_url, task in active_bots.items():
        active.append({
            "room_url": room_url,
            "is_running": not task.done()
        })
    
    return {"active_bots": active, "count": len(active)}


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable
    port = int(os.getenv('PORT', 3000))
    
    logger.info(f"🚀 Starting server on port {port}")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )