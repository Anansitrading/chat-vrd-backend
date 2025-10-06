#!/bin/bash
# Deploy Chat-VRD Backend to Railway

set -e

echo "===== Chat-VRD Backend Deployment ====="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install it:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Not logged in to Railway. Logging in..."
    railway login
fi

echo "✅ Logged in to Railway"
echo ""

# Check for required environment variables
echo "Checking environment variables..."

if [ -z "$DAILY_API_KEY" ]; then
    echo "⚠️  DAILY_API_KEY not set"
    read -p "Enter your Daily.co API key: " DAILY_API_KEY
    railway variables set DAILY_API_KEY="$DAILY_API_KEY"
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set"
    read -p "Enter your Google API key: " GOOGLE_API_KEY
    railway variables set GOOGLE_API_KEY="$GOOGLE_API_KEY"
fi

echo "✅ Environment variables configured"
echo ""

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Check logs: railway logs"
echo "2. Get URL: railway domain"
echo "3. Test: Update test-railway-backend.html with new URL"
