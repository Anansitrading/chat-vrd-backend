# Language Detection Integration Guide

## Overview

This guide explains how language detection flows from the frontend through to the Pipecat backend and Gemini Live configuration.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CLICKS MIC IN FRONTEND                                  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. DEEPGRAM LANGUAGE DETECTION (≤300ms)                        │
│    - Captures 200-300ms audio sample                            │
│    - Calls /api/deepgram-language-detect                        │
│    - Returns: { language: "nl", geminiLanguageCode: "nl-NL" }   │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. FRONTEND CALLS BACKEND /connect                             │
│    POST https://kijko-production.up.railway.app/connect         │
│    Body: { "language": "nl-NL" }                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. BACKEND CREATES DAILY ROOM & SPAWNS BOT                     │
│    - Creates Daily.co room                                      │
│    - Spawns Pipecat bot with language parameter                │
│    - Bot joins room with Gemini Live configured for language    │
│    - Returns: { room_url, token }                               │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. FRONTEND JOINS DAILY ROOM                                   │
│    - Uses DailyIframe or DailyCall to join                      │
│    - Bot is already in room with correct language configured    │
│    - Audio conversation begins                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Configuration (✅ COMPLETED)

The backend bot (`bot.py`) has been updated to accept and configure language:

```python
# bot.py - UPDATED
async def run_bot(room_url: str, token: str, language: str = "en-US"):
    """Language code in BCP-47 format (e.g., "en-US", "nl-NL")"""
    
    llm = GeminiMultimodalLiveLLMService(
        api_key=GOOGLE_API_KEY,
        voice_id="Puck",
        # ✅ Configure speech with detected language
        speech_config={
            "language_code": language,  # BCP-47 from Deepgram
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Puck"
                }
            }
        },
        # ✅ Enable transcription for proper language handling
        input_audio_transcription={},
        output_audio_transcription={},
    )
```

The `/connect` endpoint already accepts the language parameter:

```python
# server.py - ALREADY CONFIGURED
@app.post("/connect")
async def connect(request: ConnectRequest):
    # request.language defaults to "en-US" if not provided
    room_url, bot_token, client_token = await create_daily_room(request.language)
    
    # Spawn bot with language
    bot_task = asyncio.create_task(
        run_bot(room_url, bot_token, request.language)
    )
    
    return {
        "room_url": room_url,
        "token": client_token,
    }
```

## Frontend Implementation (TODO)

### Option 1: Modify `useGeminiLive` Hook

The current `useGeminiLive` hook connects directly to Google's Gemini Live API. For the Pipecat backend flow, you need a different approach. Create a new hook `usePipecatBackend`:

```typescript
// src/hooks/usePipecatBackend.ts
import { useState, useRef, useCallback } from 'react';
import DailyIframe from '@daily-co/daily-js';

export const usePipecatBackend = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dailyRef = useRef<any>(null);
  
  const connect = useCallback(async (languageCode: string) => {
    try {
      // 1. Call backend to create room and spawn bot
      const response = await fetch('https://kijko-production.up.railway.app/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: languageCode })
      });
      
      if (!response.ok) {
        throw new Error('Failed to connect to backend');
      }
      
      const { room_url, token } = await response.json();
      
      // 2. Join Daily room where bot is waiting
      dailyRef.current = DailyIframe.createCallObject();
      
      await dailyRef.current.join({
        url: room_url,
        token: token,
      });
      
      setIsConnected(true);
      return { success: true };
      
    } catch (err: any) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  }, []);
  
  const disconnect = useCallback(async () => {
    if (dailyRef.current) {
      await dailyRef.current.leave();
      await dailyRef.current.destroy();
      dailyRef.current = null;
    }
    setIsConnected(false);
  }, []);
  
  return {
    isConnected,
    error,
    connect,
    disconnect,
  };
};
```

### Option 2: Integrate into ChatInput Component

Update the mic click handler to use the backend flow:

```typescript
// src/components/ChatInput.tsx
import { useDeepgramLanguageDetection } from '../hooks/useDeepgramLanguageDetection';
import { usePipecatBackend } from '../hooks/usePipecatBackend';

export const ChatInput: React.FC<ChatInputProps> = ({ ...props }) => {
  const { detectLanguage, isDetecting } = useDeepgramLanguageDetection();
  const { connect, disconnect, isConnected } = usePipecatBackend();
  
  const handleMicClick = async () => {
    if (!isConnected) {
      try {
        // Step 1: Detect language (≤300ms)
        setShowLanguageDetection(true);
        const result = await detectLanguage();
        
        console.log('Detected language:', result.geminiLanguageCode);
        
        // Step 2: Connect to backend with detected language
        await connect(result.geminiLanguageCode);
        
        // Success - bot is now in room with correct language
        setShowLanguageDetection(false);
        
      } catch (error) {
        console.error('Failed to start conversation:', error);
        setShowLanguageDetection(false);
      }
    } else {
      // Disconnect
      await disconnect();
    }
  };
  
  // ... rest of component
};
```

## Testing the Integration

### Test Script

Use the provided test file (`test-railway-backend.html`) or create a simple test:

```javascript
// Test language detection + backend connection
async function testLanguageFlow() {
  // 1. Simulate language detection
  const detectedLanguage = "nl-NL"; // Would come from Deepgram
  
  // 2. Call backend
  const response = await fetch('https://kijko-production.up.railway.app/connect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: detectedLanguage })
  });
  
  const { room_url, token } = await response.json();
  console.log('Bot spawned in room:', room_url);
  console.log('Language configured:', detectedLanguage);
  
  // 3. Join room (bot is already there with correct language)
  // Use Daily SDK to join...
}
```

### Verification Steps

1. **Check bot logs**: Backend should log `Bot starting for room: ... with language: nl-NL`
2. **Test conversation**: Speak in the detected language
3. **Verify transcripts**: Bot should understand and respond in the correct language
4. **Check Gemini config**: Bot's Gemini Live session should have `languageCode` set

## Language Code Mapping

Deepgram returns ISO 639-1 codes, but Gemini Live expects BCP-47:

```typescript
// Frontend mapping (already in api/deepgram-language-detect.ts)
const languageMapping: Record<string, string> = {
  'nl': 'nl-NL',
  'en': 'en-US',
  'de': 'de-DE',
  'fr': 'fr-FR',
  // ... etc
};
```

This mapping is applied in the Vercel API endpoint, so the backend receives ready-to-use BCP-47 codes.

## Deployment

### Backend (Railway)

The backend is already deployed at:
```
https://kijko-production.up.railway.app
```

Required environment variables:
- `GOOGLE_API_KEY`: For Gemini Live
- `DAILY_API_KEY`: For creating Daily rooms

### Frontend (Vercel)

No changes needed to deployment - just update the frontend code to use the backend connection flow instead of direct Gemini Live connection.

## Troubleshooting

### Bot doesn't join room
- Check Railway logs for bot startup
- Verify DAILY_API_KEY is configured
- Ensure bot task is spawned (check active_bots dict)

### Wrong language detected
- Verify Deepgram API key is valid
- Check audio sample quality (16kHz, 16-bit PCM)
- Look at confidence score in detection response

### Bot speaks wrong language
- Check backend logs for language parameter
- Verify Gemini Live speech_config is set
- Confirm BCP-47 code is correct

## Next Steps

1. ✅ Backend updated to accept and use language parameter
2. ⏳ Frontend: Create `usePipecatBackend` hook
3. ⏳ Frontend: Integrate language detection with backend connection
4. ⏳ Test full flow: detection → backend → Daily room → conversation
5. ⏳ Deploy and verify in production
