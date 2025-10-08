# Cartesia Dutch TTS - Model Compatibility Guide

## Problem
When using Cartesia for Dutch TTS, you **MUST** use a Gemini model that supports the **Live API (bidiGenerateContent)**. Not all models support this!

## Error You'll See
If you use an incompatible model:
```
ERROR: gemini-2.5-flash is not found for API version v1beta, 
or is not supported for bidiGenerateContent
```

## ✅ Compatible Models (Native Audio)

These models support the Live API and work perfectly with Cartesia Dutch TTS:

| Model ID | Name | Voices | Best For |
|----------|------|--------|----------|
| `gemini-2.0-flash-exp` | Gemini 2.0 Flash Exp | 30 | Testing, Experiments |
| `gemini-live-2.5-flash` | Gemini Live 2.5 Flash | 30 | **RECOMMENDED** - Best quality |
| `gemini-2.0-flash-live-001` | Gemini 2.0 Flash Live | 30 | Stable production |
| `gemini-live-2.5-flash-preview-native-audio-09-2025` | Gemini Live 2.5 Preview | 30 | Latest features |

## ❌ Incompatible Models (Half-Cascade)

These models **DO NOT** support the Live API and will fail:

| Model ID | Name | Why It Fails |
|----------|------|--------------|
| `gemini-2.5-flash` | Gemini 2.5 Flash | No bidiGenerateContent support |
| `gemini-2.0-flash` | Gemini 2.0 Flash | No bidiGenerateContent support |
| `gemini-2.5-flash-preview-native-audio-dialog` | Gemini 2.5 Dialog | Different API endpoint |

## Architecture Explanation

### Native Audio Model (Works ✅)
```
User Audio → Gemini Live API (WebSocket) → Text → Cartesia TTS → Dutch Audio
            [bidiGenerateContent support]
```

### Half-Cascade Model (Fails ❌)
```
User Audio → Gemini Standard API → Text → Cartesia TTS → Dutch Audio
            [No WebSocket support]
```

## How to Choose the Right Model

### For Dutch Language:
1. **Select Dutch (nl-NL)** in language dropdown
2. **Use a native-audio model** (look for the green "native-audio" badge)
3. **Recommended**: `gemini-live-2.5-flash`

### For Other Languages:
- Any model works fine since Gemini handles TTS internally
- Half-cascade models (8 voices) are faster
- Native-audio models (30 voices) have better quality

## Testing Guide

### 1. Quick Test (Correct Setup)
```
Language: Dutch (Netherlands) 🇳🇱
Model: Gemini Live 2.5 Flash (30 voices)  ← Native audio
Voice: Puck - Upbeat voice
```

Expected logs:
```
✅ Cartesia bot module loaded
🇳🇱 Using Cartesia bot for Dutch TTS
✅ Cartesia TTS configured with voice: 79a125e8-cd45-4c13-8a67-188112f4dd22
✅ Gemini configured without TTS
✅ Pipeline created with Cartesia TTS
```

### 2. Wrong Setup (Will Fail)
```
Language: Dutch (Netherlands) 🇳🇱
Model: Gemini 2.5 Flash (8 voices)  ← Half-cascade ❌
Voice: Puck - Upbeat voice
```

Expected error:
```
ERROR: gemini-2.5-flash is not found for API version v1beta
```

## Why This Happens

Cartesia requires:
1. **Gemini for STT (Speech-to-Text)** ✅
2. **Gemini for LLM (Text generation)** ✅
3. **Cartesia for TTS (Text-to-Speech)** ✅

The Gemini Live API (bidiGenerateContent) provides STT + LLM in real-time over WebSocket. Half-cascade models don't support this WebSocket API, so they can't provide the STT input that Cartesia needs.

## Quick Reference

**Want Dutch with native accent?**
→ Use: `gemini-live-2.5-flash` + Dutch language + Cartesia

**Want fastest response?**
→ Use: `gemini-2.5-flash` (half-cascade) + English + Gemini TTS

**Want best audio quality?**
→ Use: `gemini-live-2.5-flash` (native-audio) + Any language

## Verification Commands

```bash
# Check if Cartesia is available
curl https://chat-vrd-backend-production.up.railway.app/health | jq '.cartesia_bot_available'

# Should return: true

# List available models
curl https://chat-vrd-backend-production.up.railway.app/models | jq '.models[] | {id, type}'

# Look for "type": "native-audio" models
```

## Summary

| Scenario | Model Type | Dutch TTS | Works? |
|----------|-----------|-----------|--------|
| Dutch + Cartesia | Native-audio | Cartesia | ✅ YES |
| Dutch + Cartesia | Half-cascade | Cartesia | ❌ NO - API error |
| English + Gemini | Native-audio | Gemini | ✅ YES |
| English + Gemini | Half-cascade | Gemini | ✅ YES |

**Golden Rule**: For Dutch with Cartesia, always use a **native-audio model**!
