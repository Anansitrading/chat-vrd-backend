#!/bin/bash

# Railway Deployment Script
# This script deploys the Pipecat backend to Railway

set -e  # Exit on error

echo "🚂 Starting Railway deployment..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check environment variables
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "⚠️  RAILWAY_TOKEN not set. Using railway login..."
    railway login
fi

# Show current status
echo ""
echo "📊 Current Railway status:"
railway status

# Deploy to Railway
echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📋 To check logs:"
echo "   railway logs"
echo ""
echo "🔗 Your service will be available at:"
echo "   https://kijko-production.up.railway.app"
