"""
Chat-VRD Pipecat Backend Server
FastAPI server that creates Daily rooms and spawns Pipecat bots
"""

import os
import asyncio
import aiohttp
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import bot modules - make them optional to prevent startup failures
try:
    from bot import run_bot
    BOT_AVAILABLE = True
    logger.info("✅ Standard bot module loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Standard bot module failed to import: {e}")
    logger.warning("⚠️  Server will start but /connect endpoint will be unavailable")
    BOT_AVAILABLE = False
    run_bot = None

# Try to import Cartesia bot for Dutch support
try:
    from bot_with_cartesia import run_bot as run_bot_cartesia
    CARTESIA_BOT_AVAILABLE = True
    logger.info("✅ Cartesia bot module loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Cartesia bot module failed to import: {e}")
    logger.warning("⚠️  Dutch language will use standard Gemini TTS")
    CARTESIA_BOT_AVAILABLE = False
    run_bot_cartesia = None

# Initialize FastAPI
app = FastAPI(title="Chat-VRD Pipecat Backend")

# CORS middleware - Fixed: allow_origins=["*"] cannot be used with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed to False to allow wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DAILY_API_KEY = os.getenv("DAILY_API_KEY")
DAILY_API_URL = "https://api.daily.co/v1"
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

# Log environment status on startup
logger.info(f"🔧 Daily API configured: {bool(DAILY_API_KEY)}")
logger.info(f"🔧 Google API configured: {bool(os.getenv('GOOGLE_API_KEY'))}")
logger.info(f"🔧 Cartesia API configured: {bool(CARTESIA_API_KEY)}")
logger.info(f"🔧 Standard bot available: {BOT_AVAILABLE}")
logger.info(f"🔧 Cartesia bot available: {CARTESIA_BOT_AVAILABLE}")

# Track active bots and their ready events
active_bots = {}
bot_ready_events = {}


class ConnectRequest(BaseModel):
    language: Optional[str] = "en-US"
    voice_id: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Run startup checks and logging"""
    logger.info("🚀 Starting Chat-VRD Pipecat Backend...")
    
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
        "service": "pipecat-gemini-bot",
        "version": "1.0.0",
        "daily_api_configured": bool(DAILY_API_KEY),
        "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "cartesia_api_configured": bool(CARTESIA_API_KEY),
        "bot_available": BOT_AVAILABLE,
        "cartesia_bot_available": CARTESIA_BOT_AVAILABLE,
        "models_available": True,  # For compatibility with frontend
    }


@app.post("/connect")
async def connect(request: ConnectRequest):
    """
    Create a Daily room and spawn a Pipecat bot
    
    This endpoint:
    1. Creates a Daily.co room
    2. Spawns a Pipecat bot that joins the room
    3. Returns room URL and client token
    """
    
    # Check if bot module is available
    if not BOT_AVAILABLE:
        logger.error("/connect called but bot module is not available")
        raise HTTPException(500, "Bot module is not available - check server logs")
    
    try:
        logger.info(f"Creating room with language: {request.language}")
        
        # Create Daily room and tokens
        room_url, bot_token, client_token = await create_daily_room(request.language)
        
        # Extract room name
        room_name = room_url.split("/")[-1]
        
        # Create event to signal when bot is ready
        ready_event = asyncio.Event()
        bot_ready_events[room_name] = ready_event
        
        # CRITICAL: Choose bot based on language
        # Use Cartesia bot for Dutch if available and API key is configured
        use_cartesia = (
            request.language == "nl-NL" and 
            CARTESIA_BOT_AVAILABLE and 
            CARTESIA_API_KEY
        )
        
        if use_cartesia:
            logger.info(f"🇳🇱 Using Cartesia bot for Dutch language")
            logger.info(f"Spawning Cartesia bot for room: {room_name} with voice: {request.voice_id or 'auto'}")
            bot_task = asyncio.create_task(
                run_bot_cartesia(room_url, bot_token, request.language, ready_event, request.voice_id)
            )
            bot_status = "cartesia_bot_spawned"
        else:
            if request.language == "nl-NL":
                logger.warning(f"⚠️  Dutch requested but using Gemini (Cartesia not available)")
            logger.info(f"Spawning standard bot for room: {room_name} with voice: {request.voice_id or 'auto'}")
            bot_task = asyncio.create_task(
                run_bot(room_url, bot_token, request.language, ready_event, request.voice_id)
            )
            bot_status = "standard_bot_spawned"
        
        # Track the bot task
        active_bots[room_name] = bot_task
        
        # Clean up completed tasks
        def cleanup_task(task):
            if room_name in active_bots:
                del active_bots[room_name]
            if room_name in bot_ready_events:
                del bot_ready_events[room_name]
            logger.info(f"Bot task cleaned up for room: {room_name}")
        
        bot_task.add_done_callback(cleanup_task)
        
        logger.info(f"Waiting for bot to join room: {room_name}")
        # Wait for bot to signal it has joined the Daily room
        await asyncio.wait_for(ready_event.wait(), timeout=10.0)
        logger.info(f"Bot successfully joined room: {room_name}")
        
        return {
            "room_url": room_url,
            "token": client_token,
            "language": request.language,
            "bot_status": bot_status,
            "model": {
                "id": "gemini-live-2.5-flash",
                "name": "Gemini Live 2.5 Flash",
                "type": "native-audio"
            },
            "voice": {
                "id": request.voice_id or "Puck",
                "description": "Selected voice"
            }
        }
    
    except Exception as e:
        logger.error(f"Error in /connect: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to create connection: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Chat-VRD Pipecat Backend",
        "endpoints": {
            "health": "/health",
            "connect": "/connect (POST)",
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
