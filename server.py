"""
Chat-VRD Pipecat Backend Server
FastAPI server that creates Daily rooms and spawns Pipecat bots
"""

import os
import asyncio
import aiohttp
import time
from fastapi import FastAPI, HTTPException, File, UploadFile
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

# Import bot module - make it optional to prevent startup failures
try:
    from bot import run_bot
    BOT_AVAILABLE = True
    logger.info("✅ Bot module loaded successfully")
except Exception as e:
    logger.warning(f"⚠️  Bot module failed to import: {e}")
    logger.warning("⚠️  Server will start but /connect endpoint will be unavailable")
    BOT_AVAILABLE = False
    run_bot = None

# Import language detection module
try:
    from language_detection import (
        detect_language_from_audio,
        get_audio_bytes_from_request,
        LanguageDetectionResponse
    )
    LANGUAGE_DETECTION_AVAILABLE = True
    logger.info("✅ Language detection module loaded")
except Exception as e:
    logger.warning(f"⚠️  Language detection module failed to import: {e}")
    LANGUAGE_DETECTION_AVAILABLE = False

# Initialize FastAPI
app = FastAPI(title="Chat-VRD Pipecat Backend")

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
logger.info(f"🔧 Deepgram API configured: {bool(os.getenv('DEEPGRAM_API_KEY'))}")
logger.info(f"🔧 Bot module available: {BOT_AVAILABLE}")
logger.info(f"🔧 Language detection available: {LANGUAGE_DETECTION_AVAILABLE}")

# Track active bots
active_bots = {}


class ConnectRequest(BaseModel):
    language: Optional[str] = "en-US"


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
        "bot_available": BOT_AVAILABLE,
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
        
        # CRITICAL: Spawn bot task to join the room
        logger.info(f"Spawning bot for room: {room_name}")
        bot_task = asyncio.create_task(
            run_bot(room_url, bot_token, request.language)
        )
        
        # Track the bot task
        active_bots[room_name] = bot_task
        
        # Clean up completed tasks
        def cleanup_task(task):
            if room_name in active_bots:
                del active_bots[room_name]
                logger.info(f"Bot task cleaned up for room: {room_name}")
        
        bot_task.add_done_callback(cleanup_task)
        
        logger.info(f"Bot spawned successfully for room: {room_name}")
        
        return {
            "room_url": room_url,
            "token": client_token,
        }
    
    except Exception as e:
        logger.error(f"Error in /connect: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to create connection: {str(e)}")


@app.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    file: Optional[UploadFile] = File(None),
    base64_audio: Optional[str] = None,
):
    """
    Detect language from audio sample using Deepgram
    
    Accepts either:
    - Multipart file upload (file parameter)
    - JSON with base64_audio field
    
    Returns detected language (BCP-47 format) with confidence and telemetry.
    Completes in ≤300ms or returns 504 timeout error.
    """
    if not LANGUAGE_DETECTION_AVAILABLE:
        logger.error("/detect-language called but module not available")
        raise HTTPException(
            status_code=503,
            detail="Language detection service unavailable"
        )
    
    try:
        # Extract audio data
        audio_data, mime_type = await get_audio_bytes_from_request(
            file=file,
            base64_audio=base64_audio
        )
        
        # Detect language with 300ms timeout
        result = await detect_language_from_audio(
            audio_data=audio_data,
            mime_type=mime_type,
            timeout_ms=300
        )
        
        logger.info(
            f"Language detection completed: {result.detected_language} "
            f"({result.duration_ms:.1f}ms)"
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /detect-language: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Chat-VRD Pipecat Backend",
        "endpoints": {
            "health": "/health",
            "connect": "/connect (POST)",
            "detect-language": "/detect-language (POST)",
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
