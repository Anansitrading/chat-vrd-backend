# Cartesia Dutch TTS Integration - Troubleshooting & Fix

## Problem Summary
Cartesia Dutch TTS was not working despite:
- ✅ CARTESIA_API_KEY set in Railway environment variables
- ✅ bot_with_cartesia.py created and coded correctly
- ✅ server_with_model_selection.py had Cartesia routing logic

## Root Cause
**Missing Dependency**: The `requirements.txt` file didn't include the `cartesia` extra for Pipecat, causing the import to fail:

```python
from pipecat.services.cartesia.tts import CartesiaHttpTTSService  # ❌ FAILED
```

## The Fix
Updated `requirements.txt` to include Cartesia support:

**Before:**
```
pipecat-ai[daily,google,silero]==0.0.87
```

**After:**
```
pipecat-ai[daily,google,silero,cartesia]==0.0.87
```

## How It Works Now

### 1. **Dependency Installation**
Railway installs Pipecat with Cartesia support during deployment.

### 2. **Bot Module Import** (server_with_model_selection.py)
```python
try:
    from bot_with_cartesia import run_bot as run_bot_cartesia
    CARTESIA_AVAILABLE = True
    logger.info("✅ Cartesia bot module loaded")
except Exception as e:
    CARTESIA_AVAILABLE = False
    logger.warning(f"⚠️ Cartesia bot not available: {e}")
```

### 3. **Language-Based Routing** (lines 372-381)
```python
use_cartesia = (
    request.language == "nl-NL" and 
    os.getenv("CARTESIA_API_KEY") and 
    CARTESIA_AVAILABLE
)

if use_cartesia:
    logger.info("🇳🇱 Using Cartesia bot for Dutch TTS")
    run_bot = run_bot_cartesia
else:
    logger.info("🌍 Using standard Gemini bot")
    run_bot = run_bot_standard
```

### 4. **Cartesia TTS Service** (bot_with_cartesia.py)
```python
tts = CartesiaHttpTTSService(
    api_key=CARTESIA_API_KEY,
    voice_id=CARTESIA_DUTCH_VOICES.get("default"),
    model="sonic-2",
    sample_rate=16000,
    params=CartesiaHttpTTSService.InputParams(
        language=Language.NL,
        speed="normal"
    )
)
```

## Verification Steps

### 1. Check Health Endpoint
```bash
curl https://chat-vrd-backend-production.up.railway.app/health | jq
```

Should return:
```json
{
  "status": "ok",
  "cartesia_api_configured": true,
  "cartesia_bot_available": true  // ✅ This should now be TRUE
}
```

### 2. Test in Browser
1. Open `test-railway-backend-with-dutch.html`
2. Select "Dutch (Netherlands) 🇳🇱" language
3. Select a model and voice
4. Click "Connect with Selected Configuration"
5. Look for logs showing "🇳🇱 Using Cartesia TTS for Dutch"

### 3. Check Railway Logs
After deployment completes, logs should show:
```
✅ Cartesia bot module loaded successfully
🔧 Cartesia API configured: True
🔧 Cartesia bot available: True
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         Frontend (HTML Test Page)           │
└─────────────────┬───────────────────────────┘
                  │ POST /connect
                  │ { language: "nl-NL", ... }
                  ▼
┌─────────────────────────────────────────────┐
│    server_with_model_selection.py           │
│                                             │
│  if language == "nl-NL" && CARTESIA_KEY:   │
│      ├─► run_bot_cartesia()                │
│  else:                                      │
│      └─► run_bot_standard()                │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
┌──────────────────┐  ┌────────────────────┐
│ bot_with_        │  │ bot_with_model_    │
│ cartesia.py      │  │ selection.py       │
│                  │  │                    │
│ Gemini (STT+LLM) │  │ Gemini (All)       │
│      +           │  │ (STT+LLM+TTS)      │
│ Cartesia (TTS)   │  │                    │
└──────────────────┘  └────────────────────┘
```

## Environment Variables Required

On Railway, these must be set:
- `DAILY_API_KEY` - For WebRTC rooms
- `GOOGLE_API_KEY` - For Gemini Live API
- `CARTESIA_API_KEY` - For Dutch TTS (without this, falls back to Gemini)

## Security Notes

- ✅ All API keys read from environment variables
- ✅ No hardcoded credentials in code
- ✅ Test files with exposed keys removed from repository
- ⚠️ Remember to rotate any previously exposed Google API keys

## Next Steps

1. Wait for Railway deployment to complete (~2-3 minutes)
2. Test the health endpoint to confirm `cartesia_bot_available: true`
3. Test Dutch language in the HTML test page
4. Listen to verify the Dutch accent sounds native (Cartesia) vs synthetic (Gemini)

## Rollback Plan

If Cartesia causes issues, you can quickly disable it by:
1. Remove `CARTESIA_API_KEY` from Railway environment variables
2. The system will automatically fall back to Gemini TTS for all languages
