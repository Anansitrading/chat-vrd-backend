# Railway Deployment - Deepgram STT + Cartesia TTS Setup

## 🚨 CRITICAL: Railway Environment Variable Setup

### 1. Add Deepgram API Key to Railway

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Select your project**: `chat-vrd-backend`
3. **Click on your service**
4. **Go to "Variables" tab**
5. **Add new variable**:
   - **Key**: `DEEPGRAM_API_KEY`
   - **Value**: Your Deepgram API key (get from https://console.deepgram.com/)

### 2. Verify Cartesia API Key Exists

Make sure this is already set in Railway:
- **Key**: `CARTESIA_API_KEY`
- **Value**: Your Cartesia API key

If not set, add it now from https://play.cartesia.ai/

### 3. Complete Environment Variables List

Your Railway service should have these variables:

| Variable | Required | Get From |
|----------|----------|----------|
| `PORT` | ✅ Auto-set by Railway | N/A |
| `DAILY_API_KEY` | ✅ Required | https://dashboard.daily.co/developers |
| `GOOGLE_API_KEY` | ✅ Required | https://aistudio.google.com/apikey |
| `DEEPGRAM_API_KEY` | ✅ **NEW - Required** | https://console.deepgram.com/ |
| `CARTESIA_API_KEY` | ✅ Required for Dutch | https://play.cartesia.ai/ |

## 🚀 Deploy Updated Code to Railway

### Option A: Direct Push to Railway (if Railway remote configured)

```bash
cd /home/david/Projects/chat-vrd-backend

# Commit changes
git add bot_with_cartesia.py .env.example DEEPGRAM_CARTESIA_IMPLEMENTATION.md
git commit -m "Fix: Replace Google STT with Deepgram STT for Dutch bot"

# Push to Railway
git push railway main
```

### Option B: Push via GitHub (if Railway is connected to GitHub)

```bash
cd /home/david/Projects/chat-vrd-backend

# Commit changes
git add bot_with_cartesia.py .env.example DEEPGRAM_CARTESIA_IMPLEMENTATION.md RAILWAY_DEEPGRAM_DEPLOYMENT.md
git commit -m "Fix: Replace Google STT with Deepgram STT for Dutch bot"

# Push to GitHub
git push origin main

# Railway will auto-deploy
```

## 🔍 Verify Deployment

### 1. Check Health Endpoint

```bash
curl https://your-railway-app.railway.app/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "pipecat-gemini-bot",
  "version": "1.0.0",
  "daily_api_configured": true,
  "google_api_configured": true,
  "cartesia_api_configured": true,
  "deepgram_api_configured": true,
  "standard_bot_available": true,
  "cartesia_bot_available": true
}
```

### 2. Check Railway Logs

Look for these success messages:

```
✅ Pipecat modules loaded successfully
✅ Model configuration loaded
🔧 Daily API configured: True
🔧 Google API configured: True
🔧 Cartesia API configured: True
🔧 Deepgram API configured: True
🇳🇱 Using Cartesia TTS for Dutch language
✅ Deepgram STT configured for Dutch with language detection
✅ Cartesia TTS configured with voice: 79a125e8-cd45-4c13-8a67-188112f4dd22
```

### 3. Test Dutch Conversation

```bash
curl -X POST https://your-railway-app.railway.app/connect \
  -H "Content-Type: application/json" \
  -d '{"language": "nl-NL", "model_id": "gemini-2.0-flash-exp"}'
```

Expected response:
```json
{
  "room_url": "https://...",
  "token": "...",
  "bot_started": true
}
```

## 🐛 Troubleshooting

### Error: "DEEPGRAM_API_KEY not configured"

**Solution:**
1. Go to Railway dashboard
2. Select your service
3. Variables tab
4. Add `DEEPGRAM_API_KEY`
5. Redeploy (Railway auto-redeploys on variable change)

### Error: "No module named 'pipecat.services.deepgram'"

**Solution:**
This means the Pipecat package needs to be reinstalled with Deepgram support.

Check your `requirements.txt` or deployment configuration:

```txt
pipecat-ai[deepgram,cartesia,google]
```

Or update it to:
```txt
pipecat-ai[daily,deepgram,cartesia,google,silero]
```

### Logs Show: "❌ Failed to import Pipecat modules"

**Solution:**
1. Check Railway build logs
2. Ensure all dependencies are installed
3. Verify `requirements.txt` is correct
4. Try manual redeploy

### Dutch Bot Still Has Errors

**Checklist:**
- ✅ `DEEPGRAM_API_KEY` set in Railway?
- ✅ `CARTESIA_API_KEY` set in Railway?
- ✅ Latest code deployed?
- ✅ Railway service restarted after adding variables?

## 📊 Expected Performance

### Latency Improvements

| Component | Latency |
|-----------|---------|
| Deepgram STT | ~100-200ms |
| Gemini LLM | ~500-1000ms |
| Cartesia TTS | ~100-200ms |
| **Total** | ~700-1400ms |

### Benefits Over Previous Setup

- ❌ **Before**: Google STT credential errors, stuttering
- ✅ **After**: Simple API key auth, smooth streaming
- ✅ **Better**: Native Dutch voice quality with Cartesia
- ✅ **Faster**: Deepgram optimized for real-time

## 🔄 Rollback Plan

If deployment fails, rollback to previous version:

```bash
# Find previous deployment
git log --oneline

# Rollback
git revert HEAD
git push railway main
```

Or use Railway dashboard:
1. Go to Deployments tab
2. Find previous working deployment
3. Click "Redeploy"

## 📝 Post-Deployment Checklist

- [ ] `DEEPGRAM_API_KEY` added to Railway
- [ ] `CARTESIA_API_KEY` verified in Railway
- [ ] Code pushed and deployed
- [ ] Health endpoint returns success
- [ ] Railway logs show no errors
- [ ] Dutch conversation tested
- [ ] No Google STT credential errors
- [ ] Audio quality is smooth (no stuttering)
- [ ] Linear issue KIJ-179 updated

## 🆘 Support

If issues persist:
1. Check Railway logs for specific errors
2. Review Linear issue: https://linear.app/kijko/issue/KIJ-179/
3. Contact: david@kijko.nl

## 🔗 Related Documentation

- [Deepgram + Cartesia Implementation Guide](./DEEPGRAM_CARTESIA_IMPLEMENTATION.md)
- [Pipecat Deepgram Docs](https://docs.pipecat.ai/server/services/stt/deepgram)
- [Cartesia API Docs](https://docs.cartesia.ai/)
- [Railway Deployment Docs](https://docs.railway.app/)
