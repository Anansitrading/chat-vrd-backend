"""
Language Detection Module using Deepgram
Provides fast language detection (≤300ms) for audio samples
"""

import os
import base64
import time
import logging
from typing import Optional
from fastapi import UploadFile, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Deepgram client - initialized on first use
_deepgram_client = None


class LanguageDetectionResponse(BaseModel):
    """Response model for language detection"""
    detected_language: str  # BCP-47 format (e.g., "en-US", "nl-NL")
    confidence: float  # 0.0 to 1.0
    duration_ms: float  # Detection processing time in milliseconds
    timestamp: float  # Unix timestamp when detection completed


def get_deepgram_client():
    """Get or create Deepgram client instance"""
    global _deepgram_client
    
    if _deepgram_client is None:
        try:
            from deepgram import DeepgramClient
            
            api_key = os.getenv("DEEPGRAM_API_KEY")
            if not api_key:
                logger.error("DEEPGRAM_API_KEY environment variable not set")
                raise RuntimeError("DEEPGRAM_API_KEY not configured")
            
            _deepgram_client = DeepgramClient(api_key)
            logger.info("✅ Deepgram client initialized")
        except ImportError:
            logger.error("deepgram-sdk not installed. Run: pip install deepgram-sdk")
            raise ImportError("deepgram-sdk package not found")
    
    return _deepgram_client


async def detect_language_from_audio(
    audio_data: bytes,
    mime_type: str = "audio/wav",
    timeout_ms: int = 300
) -> LanguageDetectionResponse:
    """
    Detect language from audio sample using Deepgram
    
    Args:
        audio_data: Raw audio bytes
        mime_type: MIME type of audio (e.g., "audio/wav", "audio/mp3")
        timeout_ms: Maximum time to wait for detection (default 300ms)
    
    Returns:
        LanguageDetectionResponse with detected language and telemetry
    
    Raises:
        HTTPException: On timeout or detection failure
    """
    import asyncio
    
    start_time = time.time()
    
    try:
        client = get_deepgram_client()
        
        # Prepare audio source
        source = {
            "buffer": audio_data,
        }
        
        # Deepgram options for language detection
        options = {
            "detect_language": True,
            "punctuate": False,
            "model": "nova-2",  # Fast model for quick detection
        }
        
        logger.info(f"🔍 Starting language detection (timeout: {timeout_ms}ms)")
        
        # Call Deepgram with timeout
        async def deepgram_call():
            response = await client.listen.prerecorded.v("1").transcribe_file(
                source,
                options
            )
            return response
        
        # Execute with timeout
        response = await asyncio.wait_for(
            deepgram_call(),
            timeout=timeout_ms / 1000.0  # Convert to seconds
        )
        
        # Parse response
        detected_lang = "und"  # undefined fallback
        confidence = 0.0
        
        # Extract language from Deepgram response
        try:
            results = response.results
            if results and results.channels:
                channel = results.channels[0]
                if channel.alternatives:
                    alt = channel.alternatives[0]
                    
                    # Try to get detected language
                    if hasattr(alt, 'detected_language'):
                        detected_lang = alt.detected_language
                    elif hasattr(alt, 'language'):
                        detected_lang = alt.language
                    
                    # Get confidence
                    if hasattr(alt, 'confidence'):
                        confidence = float(alt.confidence)
            
            # Check metadata for language info
            if detected_lang == "und" and hasattr(response, 'metadata'):
                metadata = response.metadata
                if hasattr(metadata, 'detected_language'):
                    detected_lang = metadata.detected_language
                elif hasattr(metadata, 'language'):
                    detected_lang = metadata.language
        
        except Exception as e:
            logger.warning(f"⚠️ Error parsing Deepgram response: {e}")
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"✅ Language detected: {detected_lang} "
            f"(confidence: {confidence:.2f}, duration: {duration_ms:.1f}ms)"
        )
        
        return LanguageDetectionResponse(
            detected_language=detected_lang,
            confidence=confidence,
            duration_ms=duration_ms,
            timestamp=time.time()
        )
    
    except asyncio.TimeoutError:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Language detection timed out after {duration_ms:.1f}ms")
        raise HTTPException(
            status_code=504,
            detail=f"Language detection timed out (>{timeout_ms}ms)"
        )
    
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"❌ Language detection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Language detection error: {str(e)}"
        )


async def get_audio_bytes_from_request(
    file: Optional[UploadFile] = None,
    base64_audio: Optional[str] = None,
) -> tuple[bytes, str]:
    """
    Extract audio bytes from either file upload or base64 string
    
    Returns:
        Tuple of (audio_bytes, mime_type)
    """
    if file is not None:
        audio_bytes = await file.read()
        mime_type = file.content_type or "audio/wav"
        logger.info(f"📁 Received audio file: {file.filename} ({len(audio_bytes)} bytes)")
        return audio_bytes, mime_type
    
    elif base64_audio is not None:
        try:
            audio_bytes = base64.b64decode(base64_audio)
            logger.info(f"📦 Received base64 audio ({len(audio_bytes)} bytes)")
            return audio_bytes, "audio/wav"  # Assume WAV for base64
        except Exception as e:
            logger.error(f"❌ Invalid base64 audio: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid base64 audio data"
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail="No audio data provided (file or base64_audio required)"
        )
