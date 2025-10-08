# Railway Deployment - Cartesia Dutch TTS Setup

## 1. Get Cartesia API Key

1. Go to https://cartesia.ai
2. Sign up/login
3. Go to API Keys section
4. Create a new API key
5. Copy the key

## 2. Add Environment Variable to Railway

1. Go to your Railway dashboard
2. Select your `chat-vrd-backend` project
3. Go to Variables tab
4. Add new variable:
   - **Key**: `CARTESIA_API_KEY`
   - **Value**: Your Cartesia API key

## 3. Deploy the Updated Backend

```bash
# Commit the new files
git add bot_with_cartesia.py server_with_model_selection.py
git commit -m "Add Cartesia Dutch TTS support"

# Push to Railway
git push railway main
```

Or if using GitHub:
```bash
git push origin main
# Railway will auto-deploy from GitHub
```

## 4. Verify Deployment

1. Check health endpoint:
```bash
curl https://chat-vrd-backend-production.up.railway.app/health
```

Should show:
```json
{
  "cartesia_api_configured": true,
  "cartesia_bot_available": true
}
```

2. Test Dutch connection:
```bash
curl -X POST https://chat-vrd-backend-production.up.railway.app/connect \
  -H "Content-Type: application/json" \
  -d '{"language": "nl-NL", "model_id": "gemini-2.0-flash-exp"}'
```

## 5. Environment Variables Summary

Your Railway project should have these variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `PORT` | Auto-set by Railway | Yes |
| `DAILY_API_KEY` | Daily.co API key | Yes |
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `CARTESIA_API_KEY` | Cartesia TTS API key | For Dutch |

## 6. Testing Dutch TTS

1. Open your frontend
2. Select "Dutch (Netherlands)" language
3. Connect to a room
4. The bot should now speak with native Dutch accent using Cartesia

## 7. Monitoring Logs

Watch Railway logs to confirm Cartesia is being used:

```
🇳🇱 Using Cartesia TTS for Dutch language
✅ Cartesia TTS configured with voice: 79a125e8-cd45-4c13-8a67-188112f4dd22
```

## 8. Fallback Behavior

If Cartesia API key is not set or fails:
- System falls back to Gemini TTS
- Log shows: `⚠️ CARTESIA_API_KEY not configured, falling back to Gemini TTS`

## Notes

- Only Dutch (nl-NL) uses Cartesia
- All other languages use Gemini TTS
- Cartesia uses HTTP API (not WebSocket) for compatibility with WebRTC/Daily
- Sample rate is 16kHz to match Daily transport

## Troubleshooting

If Dutch TTS doesn't work:

1. **Check API key**: Verify CARTESIA_API_KEY is set in Railway
2. **Check logs**: Look for Cartesia initialization errors
3. **Test API key**: 
```bash
curl -X POST "https://api.cartesia.ai/tts/bytes" \
  -H "X-API-Key: YOUR_KEY" \
  -H "Cartesia-Version: 2024-11-13" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "sonic-2", "transcript": "Test", "voice": {"mode": "id", "id": "79a125e8-cd45-4c13-8a67-188112f4dd22"}}'
```