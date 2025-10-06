# Quick Deployment Guide

## 📁 Backend Location
`/home/david/Projects/chat-vrd-backend/`

## ✅ What's Been Created

A complete, working Pipecat backend that:
- ✅ Creates Daily.co rooms via `/connect` endpoint
- ✅ **Automatically spawns bots that join rooms** (FIXED!)
- ✅ Uses Gemini Live API for STT/TTS/LLM
- ✅ Supports multiple languages
- ✅ Ready for Railway deployment

## 🚀 Deploy to Railway (3 Steps)

### Step 1: Get API Keys

1. **Daily.co API Key**
   - Go to: https://dashboard.daily.co/developers
   - Copy your API key

2. **Google API Key** (for Gemini)
   - Go to: https://aistudio.google.com/apikey
   - Create and copy API key

### Step 2: Deploy

```bash
cd /home/david/Projects/chat-vrd-backend

# Run deployment script
./deploy.sh
```

The script will:
1. Check if Railway CLI is installed
2. Log you in to Railway
3. Ask for your API keys
4. Deploy the backend

### Step 3: Test

1. Get your Railway URL:
   ```bash
   railway domain
   ```

2. Update test app:
   - Edit `/home/david/Projects/chat-vrd/test-railway-backend.html`
   - Change `BACKEND_URL` to your Railway URL

3. Open test app and click "Test REAL Audio + Bot Conversation"

4. **Verify bot joins:**
   - You should see: "🤖 BOT DETECTED! Bot has joined the room"
   - NOT: "❌ WARNING: Bot has NOT joined the room!"

## 🧪 Test Locally First (Recommended)

```bash
cd /home/david/Projects/chat-vrd-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run server
python server.py
```

Server starts at http://localhost:8000

Test:
```bash
curl http://localhost:8000/health
```

## 🔧 Troubleshooting

### Bot still not joining?

Check Railway logs:
```bash
railway logs
```

Look for:
- ✅ "Bot spawned successfully for room: XXX"
- ✅ "Bot joining Daily room: XXX"
- ❌ Any Python errors

### Deployment fails?

Common issues:
1. **Missing API keys** - Set in Railway dashboard
2. **Python version** - Needs Python 3.10+
3. **Railway not linked** - Run `railway link`

### Audio quality issues?

1. Check microphone permissions in browser
2. Verify Gemini API key is valid
3. Try different languages: `{"language": "nl-NL"}`

## 📝 Making Changes

### Update code:

```bash
cd /home/david/Projects/chat-vrd-backend

# Edit files (server.py, bot.py, etc.)

# Test locally first
python server.py

# Commit changes
git add .
git commit -m "Your change description"

# Deploy to Railway
railway up
```

### Or use automated script:

```bash
./deploy.sh
```

## 🎯 What Fixed the Bug

**Before:**
- `/connect` created room but NO bot joined
- Only client in room = no conversation

**After:**
- `/connect` creates room AND spawns bot task:
  ```python
  bot_task = asyncio.create_task(
      run_bot(room_url, bot_token, request.language)
  )
  ```
- Bot joins room automatically
- Client + Bot = conversation works!

## 📊 Project Structure

```
chat-vrd-backend/
├── server.py          ← FastAPI server (spawns bots)
├── bot.py            ← Pipecat bot (Gemini Live)
├── requirements.txt  ← Dependencies
├── Procfile         ← Railway start command
├── deploy.sh        ← Deployment script
├── .env.example     ← API keys template
└── README.md        ← Full documentation
```

## ⚡ Quick Commands

```bash
# Deploy
./deploy.sh

# Check logs
railway logs

# Get URL
railway domain

# Set variables
railway variables set KEY=value

# Test locally
python server.py
```

## 🆘 Need Help?

- Full docs: `README.md` in this directory
- Pipecat docs: https://docs.pipecat.ai
- Daily.co docs: https://docs.daily.co
- Railway docs: https://docs.railway.app

## ✨ Success Criteria

After deployment, the test should show:
- ✅ Health check passes
- ✅ Room created successfully  
- ✅ **Bot detected in room** (THIS WAS THE BUG!)
- ✅ Audio plays through speakers
- ✅ STT recognizes speech
- ✅ Bot responds with TTS

Good luck! 🚀
