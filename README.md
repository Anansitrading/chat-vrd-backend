# Chat-VRD Pipecat Backend

Voice conversation backend using Pipecat, Daily.co, and Google Gemini Live API.

## Architecture

```
Client (Browser) → FastAPI Server → Pipecat Bot → Daily.co Room
                                   ↓
                            Google Gemini Live API
                            (STT + LLM + TTS)
```

## Features

- ✅ FastAPI server with `/health` and `/connect` endpoints
- ✅ Automatic bot spawning when rooms are created
- ✅ Gemini Live API for multilingual STT/TTS/LLM
- ✅ Daily.co WebRTC transport
- ✅ Configurable language support

## Local Development

### 1. Install Dependencies

```bash
cd /home/david/Projects/chat-vrd-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `DAILY_API_KEY` - From https://dashboard.daily.co/developers
- `GOOGLE_API_KEY` - From https://aistudio.google.com/apikey

### 3. Run Locally

```bash
python server.py
```

Server will start at http://localhost:8000

### 4. Test Locally

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{"language": "en-US"}'
```

## Railway Deployment

### Method 1: Railway CLI

```bash
# Login to Railway
railway login

# Link to project (if already exists)
railway link

# Set environment variables
railway variables set DAILY_API_KEY=your_key_here
railway variables set GOOGLE_API_KEY=your_key_here

# Deploy
railway up
```

### Method 2: Git Push (Recommended)

```bash
# Initialize Git repo
git init
git add .
git commit -m "Initial Pipecat backend"

# Add Railway remote (get URL from Railway dashboard)
git remote add railway <your-railway-git-url>

# Push to deploy
git push railway main
```

### Method 3: GitHub Integration

1. Push code to GitHub
2. In Railway dashboard, connect GitHub repo
3. Railway will auto-deploy on push

## Environment Variables in Railway

Set these in Railway dashboard:

| Variable | Value |
|----------|-------|
| `DAILY_API_KEY` | Your Daily.co API key |
| `GOOGLE_API_KEY` | Your Google API key |
| `PORT` | Auto-set by Railway |

## API Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "pipecat-gemini-bot",
  "version": "1.0.0",
  "daily_api_configured": true,
  "google_api_configured": true
}
```

### POST /connect

Create a Daily room and spawn a bot.

**Request:**
```json
{
  "language": "en-US"  // Optional, defaults to "en-US"
}
```

**Response:**
```json
{
  "room_url": "https://yourdomain.daily.co/room-name",
  "token": "eyJhbGc..."
}
```

**Supported Languages:**
- `en-US` - English (US)
- `es-ES` - Spanish
- `fr-FR` - French
- `de-DE` - German
- `nl-NL` - Dutch
- `it-IT` - Italian

## Testing the Deployment

Use the test app at `/home/david/Projects/chat-vrd/test-railway-backend.html`

Update the `BACKEND_URL` to your Railway deployment URL.

## Troubleshooting

### Bot not joining room

Check Railway logs:
```bash
railway logs
```

Look for:
- "Bot spawned successfully for room: XXX"
- "Bot joining Daily room: XXX"

### Audio not working

1. Check browser console for errors
2. Verify microphone permissions
3. Check Daily.co room in dashboard
4. Verify GOOGLE_API_KEY is valid

### Deployment fails

Common issues:
- Missing environment variables
- Python version mismatch (use Python 3.10+)
- Dependency conflicts

## Project Structure

```
chat-vrd-backend/
├── server.py           # FastAPI server
├── bot.py             # Pipecat bot logic
├── requirements.txt   # Python dependencies
├── Procfile          # Railway startup command
├── .env.example      # Environment template
└── README.md         # This file
```

## Maintenance

### Updating Dependencies

```bash
pip install -U pipecat-ai fastapi uvicorn
pip freeze > requirements.txt
git commit -am "Update dependencies"
git push railway main
```

### Monitoring

- Railway dashboard: https://railway.app
- Daily.co dashboard: https://dashboard.daily.co
- Check logs: `railway logs --follow`

## Support

- Pipecat docs: https://docs.pipecat.ai
- Daily.co docs: https://docs.daily.co
- Gemini API docs: https://ai.google.dev

## License

MIT
