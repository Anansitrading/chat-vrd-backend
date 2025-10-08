# Deepgram STT + Cartesia TTS Implementation Guide

## Overview

This document describes the implementation of **Deepgram STT** (Speech-to-Text) and **Cartesia TTS** (Text-to-Speech) for the Chat-VRD backend, specifically for Dutch language support.

## Architecture

### Pipeline Flow

```
Audio Input → Deepgram STT → Gemini LLM → Cartesia TTS → Audio Output
```

### Components

1. **Deepgram STT** (`DeepgramSTTService`)
   - Real-time speech-to-text transcription
   - Language detection capabilities
   - Model: `nova-3` (latest)
   - Language: Dutch (`nl`)
   - Interim results enabled for real-time streaming

2. **Google Gemini LLM** (`GoogleLLMService`)
   - Text-based language model
   - Model: `gemini-2.0-flash-exp`
   - Handles conversation logic and response generation

3. **Cartesia TTS** (`CartesiaHttpTTSService`)
   - High-quality Dutch text-to-speech
   - Model: `sonic-2`
   - Voice ID: `79a125e8-cd45-4c13-8a67-188112f4dd22` (Dutch female)

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Required API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key_here
CARTESIA_API_KEY=your_cartesia_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DAILY_API_KEY=your_daily_api_key_here

# Optional
PORT=8080
```

### Getting API Keys

1. **Deepgram API Key**
   - Sign up at: https://console.deepgram.com/
   - Navigate to API Keys section
   - Create a new key

2. **Cartesia API Key**
   - Sign up at: https://play.cartesia.ai/
   - Access your dashboard
   - Generate API key

3. **Google API Key**
   - Visit: https://aistudio.google.com/apikey
   - Create new API key

4. **Daily.co API Key**
   - Dashboard: https://dashboard.daily.co/developers
   - Create new API key

## Code Implementation

### Deepgram STT Configuration

```python
from pipecat.services.deepgram.stt import DeepgramSTTService

stt = DeepgramSTTService(
    api_key=DEEPGRAM_API_KEY,
    model="nova-3",           # Latest Deepgram model
    language="nl",            # Dutch (2-letter ISO code)
    detect_language=True,     # Enable automatic language detection
    interim_results=True,     # Get live partial transcriptions
)
```

### Cartesia TTS Configuration

```python
from pipecat.services.cartesia.tts import CartesiaHttpTTSService
from pipecat.transcriptions.language import Language

tts = CartesiaHttpTTSService(
    api_key=CARTESIA_API_KEY,
    voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",  # Dutch female
    model="sonic-2",
    sample_rate=16000,
    params=CartesiaHttpTTSService.InputParams(
        language=Language.NL,
        speed="normal"
    )
)
```

### Complete Pipeline

```python
from pipecat.pipeline.pipeline import Pipeline

pipeline = Pipeline([
    transport.input(),              # Daily audio input
    stt,                           # Deepgram STT
    transcript.user(),              # Capture user transcripts
    context_aggregator.user(),      # User context
    llm,                           # Google Gemini LLM (text)
    tts,                           # Cartesia TTS
    transport.output(),            # Daily audio output
    transcript.assistant(),        # Capture bot transcripts
    context_aggregator.assistant(), # Assistant context
])
```

## Benefits

### Why Deepgram over Google STT?

1. **No credential complexity**: Simple API key authentication
2. **Built-in language detection**: Automatic language identification
3. **Lower latency**: Optimized for real-time streaming
4. **Better accuracy**: Enterprise-grade transcription
5. **Cost-effective**: Competitive pricing model

### Why Cartesia for Dutch TTS?

1. **Native Dutch voices**: High-quality, natural-sounding
2. **Low latency**: `sonic-2` model optimized for speed
3. **Emotional range**: Better expression than generic TTS
4. **Easy integration**: Simple HTTP API

## Testing

### Prerequisites

1. Set all environment variables
2. Ensure Pipecat dependencies installed:
   ```bash
   pip install pipecat-ai[deepgram,cartesia,google]
   ```

### Test Commands

1. **Import test**:
   ```bash
   python3 -c "from bot_with_cartesia import run_bot; print('✅ Import successful')"
   ```

2. **Start server**:
   ```bash
   python3 server.py
   ```

3. **Test Dutch conversation**:
   - Connect to Daily room
   - Speak in Dutch
   - Verify bot responds in Dutch

### Expected Behavior

- ✅ User speaks in Dutch → Deepgram transcribes
- ✅ Gemini generates Dutch response
- ✅ Cartesia speaks response with natural Dutch voice
- ✅ No authentication errors
- ✅ Low latency (< 500ms for transcription)

## Troubleshooting

### Common Issues

1. **`No module named 'pipecat'`**
   ```bash
   pip install pipecat-ai[deepgram,cartesia,google]
   ```

2. **`DEEPGRAM_API_KEY not configured`**
   - Check `.env` file exists
   - Verify API key is set correctly
   - Restart server after adding key

3. **`429 Rate Limit Error`**
   - Check Deepgram account usage
   - Upgrade plan if needed

4. **Stuttering audio**
   - Check network connection
   - Verify sample rate matches (16kHz)
   - Consider upgrading Deepgram model

### Debug Logs

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### Deepgram Settings

```python
stt = DeepgramSTTService(
    api_key=DEEPGRAM_API_KEY,
    model="nova-3",           # Or "base" for lower cost
    language="nl",
    detect_language=False,    # Disable if only Dutch needed
    interim_results=True,     # Keep for responsiveness
)
```

### Cartesia Settings

```python
tts = CartesiaHttpTTSService(
    api_key=CARTESIA_API_KEY,
    voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",
    model="sonic-2",          # Fastest model
    sample_rate=16000,        # Match Daily.co settings
    params=CartesiaHttpTTSService.InputParams(
        language=Language.NL,
        speed="fast"          # Speed up slightly if needed
    )
)
```

## Cartesia Voice Options

### Available Dutch Voices

```python
CARTESIA_DUTCH_VOICES = {
    "male": "95856005-0332-41b0-935f-352e296aa0df",
    "female": "79a125e8-cd45-4c13-8a67-188112f4dd22",
    "default": "79a125e8-cd45-4c13-8a67-188112f4dd22",
}
```

To change voice, update the `voice_id` parameter in TTS configuration.

## Cost Estimates

### Deepgram Pricing (as of 2024)
- **nova-3**: ~$0.0043/min
- **base**: ~$0.0036/min
- Free tier: 45,000 minutes/year

### Cartesia Pricing
- **sonic-2**: ~$0.002/min
- Free tier available

### Comparison
- **Before** (Google STT + Gemini TTS): ~$0.006/min
- **After** (Deepgram STT + Cartesia TTS): ~$0.0063/min
- **Benefit**: Better quality, easier setup

## Future Enhancements

1. **Multi-language support**
   - Extend to German (`de`), French (`fr`)
   - Use Deepgram language detection
   - Map detected language to Cartesia voices

2. **Voice customization**
   - Allow user voice selection
   - Dynamic voice switching
   - Custom pronunciation

3. **Performance monitoring**
   - Track latency metrics
   - Monitor API usage
   - Alert on errors

## References

- [Deepgram Documentation](https://developers.deepgram.com/)
- [Cartesia API Docs](https://docs.cartesia.ai/)
- [Pipecat Framework](https://docs.pipecat.ai/)
- [Linear Issue KIJ-179](https://linear.app/kijko/issue/KIJ-179/)

## Support

For issues or questions:
1. Check logs in `/var/log/chat-vrd-backend/`
2. Review Linear issue KIJ-179
3. Contact: david@kijko.nl
