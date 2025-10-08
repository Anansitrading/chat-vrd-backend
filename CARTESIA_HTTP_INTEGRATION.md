# Cartesia HTTP TTS Integration for Dutch (WebRTC/Daily Transport)

## Overview
Use Cartesia's **HTTP API** (not WebSocket) for Dutch TTS with your existing Daily WebRTC transport. No WebSocket bullshit - just simple HTTP calls that work seamlessly with Daily.

## Why HTTP API?
- **Works perfectly with Daily WebRTC transport** - no WebSocket conflicts
- **Simple integration** - just drop it in the pipeline
- **Proven to work** - Pipecat examples show it working

## Quick Implementation

### 1. Install Cartesia Support
```bash
pip install pipecat-ai[cartesia]
```

### 2. Add Cartesia API Key
```bash
# Add to .env or Railway vars
CARTESIA_API_KEY=your_key_here
```

### 3. Create Dutch TTS Service
```python
# bot_with_cartesia_dutch.py
import os
from pipecat.services.cartesia.tts import CartesiaHttpTTSService
from pipecat.transcriptions.language import Language

def create_dutch_tts():
    """Create Cartesia TTS for Dutch with HTTP API"""
    return CartesiaHttpTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # Dutch voice
        model="sonic-2",
        sample_rate=16000,  # Match Daily's sample rate
        params=CartesiaHttpTTSService.InputParams(
            language=Language.NL,
            speed="normal"
        )
    )
```

### 4. Modify Pipeline for Dutch
```python
async def run_bot(room_url: str, token: str, language: str, model_id: str):
    """Run bot with Cartesia for Dutch, Gemini for others"""
    
    # Create transport (Daily WebRTC)
    transport = DailyTransport(
        room_url,
        token,
        "Chat-VRD Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        )
    )
    
    # Choose TTS based on language
    if language == "nl-NL":
        # Use Cartesia HTTP for Dutch
        from pipecat.services.cartesia.tts import CartesiaHttpTTSService
        
        tts = CartesiaHttpTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"),
            voice_id="YOUR_DUTCH_VOICE_ID",  # Get from Cartesia
            model="sonic-2",
            sample_rate=16000,
            params=CartesiaHttpTTSService.InputParams(
                language=Language.NL
            )
        )
        
        # For Live API models - disable Gemini TTS
        if "live" in model_id or "flash" in model_id:
            llm = GeminiMultimodalLiveLLMService(
                api_key=GOOGLE_API_KEY,
                model=model_id,
                voice_id=None,  # DISABLE Gemini TTS
                system_instruction=dutch_system_prompt,
                transcribe_user_audio=True,
                transcribe_model_audio=False  # We handle TTS separately
            )
            
            # Pipeline: Gemini (STT+LLM) → Cartesia TTS
            pipeline = Pipeline([
                transport.input(),
                llm,  # Gemini for STT and LLM only
                tts,  # Cartesia for Dutch TTS
                transport.output()
            ])
    else:
        # Use standard Gemini pipeline for other languages
        llm = GeminiMultimodalLiveLLMService(
            api_key=GOOGLE_API_KEY,
            model=model_id,
            voice_id=voice_id,  # Use Gemini voices
            system_instruction=system_instruction,
            transcribe_user_audio=True,
            transcribe_model_audio=True
        )
        
        pipeline = Pipeline([
            transport.input(),
            llm,  # Gemini handles everything
            transport.output()
        ])
```

### 5. Get Dutch Voice IDs
```python
# test_cartesia_voices.py
import asyncio
from cartesia import AsyncCartesia
import os

async def list_dutch_voices():
    client = AsyncCartesia(api_key=os.getenv("CARTESIA_API_KEY"))
    voices = await client.voices.list()
    
    print("Available Cartesia Voices:")
    for voice in voices:
        print(f"ID: {voice['id']}")
        print(f"Name: {voice['name']}")
        print(f"Languages: {voice.get('language', 'unknown')}")
        print(f"Description: {voice.get('description', '')}")
        print("---")
    
    await client.close()

asyncio.run(list_dutch_voices())
```

### 6. Server Endpoint Update
```python
# server_with_model_selection.py
@app.post("/connect")
async def connect_to_room(request: Request):
    data = await request.json()
    room_url = data.get("room_url")
    language = data.get("language", "en-US")
    model = data.get("model", "gemini-2.0-flash-exp")
    
    # Pass TTS choice to bot
    use_cartesia = language == "nl-NL"
    
    bot_task = asyncio.create_task(
        run_bot_process(
            room_url,
            token,
            language,
            model,
            use_cartesia_tts=use_cartesia
        )
    )
```

## Complete Working Example

```python
# bot_with_cartesia_dutch_complete.py
import os
import asyncio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.cartesia.tts import CartesiaHttpTTSService
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transcriptions.language import Language

async def run_dutch_bot(room_url: str, token: str):
    """Bot with Cartesia Dutch TTS + Gemini Live"""
    
    # Daily transport (WebRTC)
    transport = DailyTransport(
        room_url,
        token,
        "Dutch Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        )
    )
    
    # Gemini for STT + LLM (NO TTS)
    llm = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash-exp",
        voice_id=None,  # DISABLE Gemini TTS
        system_instruction="Je bent een behulpzame Nederlandse assistent.",
        transcribe_user_audio=True,
        transcribe_model_audio=False
    )
    
    # Cartesia for Dutch TTS
    tts = CartesiaHttpTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="YOUR_DUTCH_VOICE_ID",
        model="sonic-2",
        sample_rate=16000,
        params=CartesiaHttpTTSService.InputParams(
            language=Language.NL
        )
    )
    
    # Pipeline
    pipeline = Pipeline([
        transport.input(),
        llm,  # Gemini STT + LLM
        tts,  # Cartesia TTS
        transport.output()
    ])
    
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True
        )
    )
    
    @transport.event_handler("on_joined")
    async def on_joined(transport, event):
        print("Bot joined room!")
    
    await task.run()
```

## Testing

1. **Test Cartesia Connection**
```bash
curl -X POST "https://api.cartesia.ai/tts/bytes" \
  -H "X-API-Key: $CARTESIA_API_KEY" \
  -H "Cartesia-Version: 2024-11-13" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "sonic-2",
    "transcript": "Hallo, dit is een test.",
    "voice": {"mode": "id", "id": "YOUR_VOICE_ID"},
    "output_format": {"container": "raw", "encoding": "pcm_s16le", "sample_rate": 16000},
    "language": "nl"
  }' --output test.raw
```

2. **Play test audio**
```bash
ffplay -f s16le -ar 16000 -ac 1 test.raw
```

## Key Points

✅ **No WebSocket issues** - Uses simple HTTP API
✅ **Works with Daily WebRTC** - Proven in Pipecat examples
✅ **Simple integration** - Just swap TTS service in pipeline
✅ **Low latency** - HTTP streaming still fast enough
✅ **Fallback ready** - Can fallback to Gemini if needed

## Deployment

1. Add `CARTESIA_API_KEY` to Railway variables
2. Deploy updated bot code
3. Test with Dutch language selection

That's it! No WebSocket complexity, just simple HTTP that works with your WebRTC setup.