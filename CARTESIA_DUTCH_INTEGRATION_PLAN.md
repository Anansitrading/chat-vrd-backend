# Cartesia TTS Integration Plan for Dutch Language Support

## Overview
Replace Gemini's TTS with Cartesia for Dutch language to achieve native-sounding speech with low latency. Cartesia will handle TTS for both Live API models and regular Gemini Pro models when Dutch is selected.

## Architecture Design

### 1. Hybrid TTS Approach
```
User selects language (nl-NL) 
    ↓
If Dutch detected:
    → Use Cartesia TTS (WebSocket)
    → Disable Gemini TTS
    → Keep Gemini for STT and LLM
Else:
    → Use Gemini native TTS
```

### 2. Key Components

#### A. Cartesia Service Integration
```python
# New file: cartesia_tts_service.py
from pipecat.services.cartesia.tts import CartesiaTTSService

class DutchCartesiaTTSService:
    def __init__(self, api_key: str):
        self.tts = CartesiaTTSService(
            api_key=api_key,
            voice_id="dutch_voice_id",  # Select Dutch native voice
            model="sonic-2",
            sample_rate=16000,  # Match Gemini's sample rate
            params=CartesiaTTSService.InputParams(
                language=Language.NL,
                speed="normal"
            )
        )
```

#### B. Pipeline Modification
For Dutch language, the pipeline will be:
1. **Live API Models**: Daily Input → Gemini STT → Gemini LLM → Cartesia TTS → Daily Output
2. **Pro Models**: Daily Input → Deepgram STT → Gemini Pro LLM → Cartesia TTS → Daily Output

## Implementation Steps

### Phase 1: Environment Setup
1. **Add Cartesia API Key**
   ```bash
   # Add to .env
   CARTESIA_API_KEY=your_cartesia_api_key
   ```

2. **Install Dependencies**
   ```bash
   pip install pipecat-ai[cartesia]
   ```

### Phase 2: Voice Selection
1. **Fetch Available Dutch Voices**
   ```python
   # cartesia_voices.py
   async def get_dutch_voices():
       client = AsyncCartesia(api_key=os.getenv("CARTESIA_API_KEY"))
       voices = await client.voices.list()
       dutch_voices = [v for v in voices if "nl" in v.languages or "dutch" in v.name.lower()]
       return dutch_voices
   ```

2. **Select Best Dutch Voice**
   - Test voices for naturalness
   - Consider male/female options
   - Store selected voice_id in config

### Phase 3: Service Integration

#### A. Create Cartesia TTS Wrapper
```python
# services/cartesia_dutch.py
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.transcriptions.language import Language

class CartesiaDutchTTS:
    DUTCH_VOICES = {
        "male": "voice_id_male_dutch",
        "female": "voice_id_female_dutch",
        "neutral": "voice_id_neutral_dutch"
    }
    
    def __init__(self, voice_type="neutral"):
        self.service = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"),
            voice_id=self.DUTCH_VOICES[voice_type],
            model="sonic-2",
            sample_rate=16000,
            params=CartesiaTTSService.InputParams(
                language=Language.NL
            )
        )
```

#### B. Modify Bot Pipeline
```python
# bot_with_cartesia_dutch.py
async def create_pipeline(language: str, model_id: str):
    if language == "nl-NL":
        # Use Cartesia for Dutch TTS
        tts = CartesiaDutchTTS(voice_type="neutral").service
        
        if "live" in model_id or "flash" in model_id:
            # For Live API models
            llm = GeminiMultimodalLiveLLMService(
                api_key=GOOGLE_API_KEY,
                model=model_id,
                voice_id=None,  # Disable Gemini TTS
                system_instruction=dutch_instructions,
                transcribe_user_audio=True,
                transcribe_model_audio=False  # Don't transcribe since we use Cartesia
            )
        else:
            # For Pro models
            llm = GoogleLLMService(
                api_key=GOOGLE_API_KEY,
                model=model_id,
                system_instruction=dutch_instructions
            )
            
        return Pipeline([
            transport.input(),
            llm,  # Gemini for STT/LLM
            tts,  # Cartesia for TTS
            transport.output()
        ])
    else:
        # Use standard Gemini pipeline for other languages
        return create_standard_pipeline(language, model_id)
```

### Phase 4: Server Endpoint Updates

#### Update `/connect` Endpoint
```python
@app.post("/connect")
async def connect_to_room(request: Request):
    data = await request.json()
    language = data.get("language", "en-US")
    model_id = data.get("model", "gemini-2.0-flash-exp")
    
    # Determine TTS service
    if language == "nl-NL":
        tts_service = "cartesia"
        logger.info("Using Cartesia TTS for Dutch")
    else:
        tts_service = "gemini"
    
    # Start bot with appropriate TTS
    bot_process = await start_bot_process(
        room_url, 
        token, 
        language, 
        model_id,
        tts_service=tts_service
    )
```

### Phase 5: Audio Processing Considerations

1. **Sample Rate Alignment**
   - Ensure Cartesia outputs at 16kHz to match Daily/Gemini
   - Handle any necessary resampling

2. **Latency Optimization**
   - Use WebSocket connection for streaming
   - Implement connection pooling
   - Pre-warm connections

3. **Audio Context Management**
   ```python
   # Manage audio contexts for smooth transitions
   class AudioContextManager:
       def __init__(self):
           self.cartesia_context = None
           self.gemini_context = None
           
       async def switch_to_cartesia(self):
           # Flush Gemini audio
           if self.gemini_context:
               await self.gemini_context.flush()
           # Initialize Cartesia context
           self.cartesia_context = await create_cartesia_context()
   ```

### Phase 6: Testing Strategy

1. **Unit Tests**
   - Test Cartesia voice initialization
   - Test language detection logic
   - Test pipeline switching

2. **Integration Tests**
   - Test Dutch conversation flow
   - Test language switching mid-conversation
   - Test interruption handling

3. **Performance Tests**
   - Measure TTS latency
   - Compare with Gemini TTS
   - Test under load

### Phase 7: Deployment

1. **Railway Configuration**
   ```yaml
   # railway.toml
   [variables]
   CARTESIA_API_KEY = "$CARTESIA_API_KEY"
   ```

2. **Update Documentation**
   - Add Dutch language support notes
   - Document Cartesia configuration
   - Update API documentation

## Configuration File Updates

### models_config.py
```python
# Add Cartesia configuration
CARTESIA_CONFIG = {
    "dutch_voices": {
        "default": "voice_id_here",
        "male": "male_voice_id",
        "female": "female_voice_id"
    },
    "sample_rate": 16000,
    "model": "sonic-2"
}

# Update model configurations to support hybrid TTS
def get_tts_service(language: str, model_id: str):
    if language == "nl-NL":
        return "cartesia"
    return "gemini"
```

## Error Handling

1. **Fallback Strategy**
   ```python
   async def get_tts_service(language):
       if language == "nl-NL":
           try:
               return await create_cartesia_tts()
           except Exception as e:
               logger.warning(f"Cartesia unavailable: {e}, falling back to Gemini")
               return await create_gemini_tts()
   ```

2. **Connection Management**
   - Implement reconnection logic
   - Handle WebSocket disconnections
   - Queue management during switches

## Monitoring & Metrics

1. **Track Performance**
   - TTS latency per service
   - Audio quality metrics
   - Error rates

2. **User Feedback**
   - A/B test Dutch voices
   - Collect naturalness ratings
   - Monitor conversation completion rates

## Timeline

- **Week 1**: Environment setup, voice selection
- **Week 2**: Core integration, pipeline modification
- **Week 3**: Testing, optimization
- **Week 4**: Deployment, monitoring

## Success Criteria

1. Dutch TTS sounds native (user feedback > 4.5/5)
2. Latency < 200ms for first audio chunk
3. Seamless language switching
4. No increase in error rates
5. Successful handling of 100+ concurrent Dutch conversations

## Next Steps

1. Obtain Cartesia API key
2. Test available Dutch voices
3. Implement Phase 1-2
4. Create proof of concept with single Dutch conversation
5. Iterate based on audio quality feedback