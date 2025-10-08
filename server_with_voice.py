"""
Chat-VRD Pipecat Backend Server with Voice Selection
FastAPI server that creates Daily rooms and spawns Pipecat bots with selectable voices
"""

import os
import asyncio
import aiohttp
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import bot module with voice support
try:
    from bot_with_voice_selection import run_bot, get_available_voices, get_voice_info, GEMINI_VOICES
    BOT_AVAILABLE = True
    logger.info("✅ Bot module with voice selection loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Bot module failed to import: {e}")
    logger.warning("⚠️  Server will start but /connect endpoint will be unavailable")
    BOT_AVAILABLE = False
    run_bot = None
    get_available_voices = lambda: []
    get_voice_info = lambda x: None
    GEMINI_VOICES = {}

# Initialize FastAPI
app = FastAPI(title="Chat-VRD Pipecat Backend with Voice Selection")

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

# Track active bots and their ready events
active_bots = {}
bot_ready_events = {}


class ConnectRequest(BaseModel):
    language: Optional[str] = "en-US"
    voice_id: Optional[str] = None  # Add voice selection


class VoiceInfo(BaseModel):
    id: str
    name: str
    description: str
    languages: List[str]


@app.on_event("startup")
async def startup_event():
    """Run startup checks and logging"""
    logger.info("🚀 Starting Chat-VRD Pipecat Backend with Voice Selection...")
    
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
    
    # Log available voices
    if BOT_AVAILABLE:
        voices = get_available_voices()
        logger.info(f"🎤 Available Gemini voices: {voices}")
    
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
        "service": "pipecat-gemini-bot-with-voice",
        "version": "1.1.0",
        "daily_api_configured": bool(DAILY_API_KEY),
        "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "bot_available": BOT_AVAILABLE,
        "voices_available": get_available_voices() if BOT_AVAILABLE else []
    }


@app.get("/voices")
async def list_voices():
    """Get list of available voices"""
    if not BOT_AVAILABLE:
        raise HTTPException(503, "Bot module not available")
    
    voices = []
    for voice_id, info in GEMINI_VOICES.items():
        voices.append(VoiceInfo(
            id=voice_id,
            name=info["name"],
            description=info["description"],
            languages=info["languages"]
        ))
    
    return {
        "voices": voices,
        "default": "Puck"
    }


@app.get("/voices/{voice_id}")
async def get_voice_details(voice_id: str):
    """Get details about a specific voice"""
    if not BOT_AVAILABLE:
        raise HTTPException(503, "Bot module not available")
    
    voice_info = get_voice_info(voice_id)
    if not voice_info:
        raise HTTPException(404, f"Voice '{voice_id}' not found")
    
    return VoiceInfo(
        id=voice_id,
        name=voice_info["name"],
        description=voice_info["description"],
        languages=voice_info["languages"]
    )


@app.post("/connect")
async def connect(request: ConnectRequest):
    """
    Create a Daily room and spawn a Pipecat bot with selected voice
    
    This endpoint:
    1. Creates a Daily.co room
    2. Spawns a Pipecat bot with the selected voice that joins the room
    3. Returns room URL and client token
    """
    
    # Check if bot module is available
    if not BOT_AVAILABLE:
        raise HTTPException(503, "Bot module not available - check server logs")
    
    # Validate voice if specified
    if request.voice_id:
        if request.voice_id not in GEMINI_VOICES:
            available = list(GEMINI_VOICES.keys())
            raise HTTPException(
                400, 
                f"Invalid voice_id '{request.voice_id}'. Available voices: {available}"
            )
        logger.info(f"🎤 User requested voice: {request.voice_id}")
    
    try:
        # Create Daily room
        logger.info(f"📞 Creating Daily room for language: {request.language}, voice: {request.voice_id}")
        room_url, bot_token, client_token = await create_daily_room(request.language)
        logger.info(f"✅ Daily room created: {room_url}")
        
        # Create event for bot readiness
        ready_event = asyncio.Event()
        bot_ready_events[room_url] = ready_event
        
        # Spawn bot task with selected voice
        bot_task = asyncio.create_task(
            run_bot(
                room_url, 
                bot_token, 
                request.language,
                request.voice_id,  # Pass the selected voice
                ready_event
            )
        )
        active_bots[room_url] = bot_task
        logger.info(f"🤖 Bot task spawned for room: {room_url} with voice: {request.voice_id or 'default'}")
        
        # Wait for bot to join (with timeout)
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=10.0)
            logger.info(f"✅ Bot successfully joined room: {room_url}")
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Bot joining timeout for room: {room_url}")
            # Continue anyway - bot might still join
        
        # Clean up event
        del bot_ready_events[room_url]
        
        return {
            "room_url": room_url,
            "token": client_token,
            "language": request.language,
            "voice": request.voice_id or "default",
            "voice_info": get_voice_info(request.voice_id) if request.voice_id else None,
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
            "running": not task.done(),
            "cancelled": task.cancelled() if task.done() else False
        })
    
    return {"active_bots": active, "count": len(active)}


# Run with uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '127.0.0.1')
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)