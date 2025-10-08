# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat-VRD Backend is a voice conversation system using **Pipecat** (conversational AI framework), **Daily.co** (WebRTC), and **Google Gemini Live API** (STT+LLM+TTS). The server spawns AI bots that join Daily rooms for real-time voice conversations.

**Architecture**: Client (Browser) → FastAPI Server → Pipecat Bot → Daily.co Room → Gemini Live API

## Core Components

### server.py - FastAPI Server
- **GET /health**: Health check showing API configuration status
- **POST /connect**: Creates Daily room, spawns bot, returns room URL and client token
  - Accepts `language` (BCP-47 code like "en-US", "nl-NL") and optional `voice_id`
  - Creates three tokens: room, bot_token (with owner privileges), client_token
  - Spawns bot as async task via `run_bot()` and waits for bot to join before returning
  - Manages bot lifecycle with cleanup callbacks

Key patterns:
- Bot spawning uses `asyncio.create_task()` and `asyncio.Event()` to signal readiness
- `ready_event.wait()` blocks /connect until bot joins the Daily room (10s timeout)
- Bot tasks are tracked in `active_bots` dict and cleaned up on completion

### bot.py - Pipecat Bot Logic
- Connects to Daily room using DailyTransport
- Configures GeminiMultimodalLiveLLMService with voice selection
- Creates pipeline: `transport.input() → context_aggregator → transcript → llm → transport.output()`
- Gemini handles STT/TTS/VAD internally; no separate VAD needed
- TranscriptProcessor captures both user and assistant transcripts
- Forwards transcripts to frontend via `transport._call.sendAppMessage()`

Voice selection:
- 30 available Gemini voices (see `GEMINI_VOICES` list in bot.py:44-50)
- `get_voice_for_language()` maps BCP-47 codes to voices (bot.py:53-76)
- Can override with explicit `voice_id` parameter

Event handlers:
- `on_joined`: Signals ready_event when bot joins room
- `on_first_participant_joined`: Starts conversation context
- `on_participant_left`: Sends EndFrame to clean up
- `on_transcript_update`: Forwards transcripts to frontend via Daily app messages

## Development Commands

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with DAILY_API_KEY and GOOGLE_API_KEY

# Run server (starts on port 8000 or $PORT)
python server.py

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/connect -H "Content-Type: application/json" -d '{"language": "en-US"}'
```

### Deployment (Railway)
```bash
# Deploy with CLI
railway login
railway link  # if project exists
railway variables set DAILY_API_KEY=xxx GOOGLE_API_KEY=xxx
railway up

# Or use automated script
./deploy.sh

# Monitor
railway logs --follow
railway domain  # get deployment URL
```

## Critical Architecture Details

### Bot Lifecycle Management
The most critical bug fix in this codebase (see DEPLOYMENT_GUIDE.md:139-153):
- `/connect` MUST spawn bot via `asyncio.create_task(run_bot(...))`
- Must wait for bot to join before returning room info to client
- Without bot spawning, client joins empty room with no conversation partner

### Gemini Live Integration
- Gemini Live is a unified STT+LLM+TTS service - do NOT add separate STT/TTS services
- Enable transcription: `transcribe_user_audio=True` and `transcribe_model_audio=True`
- Pipeline requires `context_aggregator` - create via `llm.create_context_aggregator(context)`
- Pipeline order matters: input → user aggregator → user transcript → llm → output → assistant transcript → assistant aggregator

### Daily.co Token Types
- **Bot token**: `is_owner: True` - gives bot admin privileges to manage room
- **Client token**: standard user token for frontend
- Tokens are room-specific and expire after 1 hour

### Transcript Forwarding
Transcripts are sent to frontend via Daily's app message system:
```python
message_data = {
    "type": "transcript",
    "text": msg.content,
    "speaker": msg.role,  # "user" or "assistant"
    "timestamp": msg.timestamp
}
await transport._call.sendAppMessage(message_data)
```

## Environment Variables

Required:
- `DAILY_API_KEY` - From https://dashboard.daily.co/developers
- `GOOGLE_API_KEY` - From https://aistudio.google.com/apikey

Optional:
- `PORT` - Server port (Railway auto-sets this)

## Supported Languages

The system supports multilingual conversations via Gemini Live. Language is specified as BCP-47 code in `/connect` request:
- `en-US` - English (US) - default, voice: Puck
- `en-GB` - English (UK) - voice: Charon
- `nl-NL` - Dutch - voice: Aoede
- `es-ES` - Spanish - voice: Fenrir
- `fr-FR` - French - voice: Kore
- `de-DE` - German - voice: Orbit
- `it-IT` - Italian - voice: Puck (default)
- `pt-BR` - Portuguese - voice: Puck (default)

## File Variants

The project contains multiple versions of core files (experimentation artifacts):
- `bot.py` - Current working version
- `bot_updated.py`, `bot_with_voice_selection.py` - Experimental variants
- `server.py` - Current working version
- `server_with_voice.py` - Experimental variant with voice selection

Always use `server.py` and `bot.py` unless explicitly working on new features in variant files.

## Testing

Test server locally:
```bash
python test_server.py
```

Test with HTML client:
- Use `test-railway-backend-with-voices.html` for full integration testing
- Update `BACKEND_URL` to target local or Railway deployment

## Dependencies

Key packages:
- `pipecat-ai[daily,google,silero]==0.0.87` - Conversational AI framework with Daily and Google integrations
- `fastapi==0.115.5` - Web framework
- `uvicorn[standard]==0.34.0` - ASGI server
- `google-genai` - Gemini API client (auto-resolved version)
- `aiohttp` - Async HTTP client for Daily API calls

Note: `onnxruntime` is included for Silero VAD (not actively used, as Gemini handles VAD internally).

## Logging

Both server and bot use Python's logging module with INFO level. Key log patterns:
- `✅` prefix for successful operations
- `⚠️` prefix for warnings
- `❌` prefix for errors
- `🔧` prefix for configuration
- `🚀` prefix for startup events
- `📝` prefix for transcripts
- `🤖` prefix for bot operations

## Troubleshooting

Bot not joining room:
- Check logs for "Bot spawned successfully for room: XXX"
- Verify `ready_event.wait()` doesn't timeout (10s limit)
- Ensure bot task isn't failing silently (check exc_info logs)

Audio not working:
- Verify GOOGLE_API_KEY is valid and has Gemini API enabled
- Check browser microphone permissions
- Verify Gemini Live API supports the requested language

Deployment issues:
- Ensure Python 3.10+ is used
- Verify all environment variables are set in Railway dashboard
- Check Procfile uses correct command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
