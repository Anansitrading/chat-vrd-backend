#!/bin/bash

echo "======================================================================="
echo "TESTING GEMINI LIVE API MODELS - REAL CONNECTION TEST"
echo "======================================================================="
echo ""

API_KEY="AIzaSyBgqJNUGO7MdiTavnqDbrbgY536kmBc1ug"

# Models to test
models=(
    "gemini-2.0-flash-exp"
    "gemini-2.5-flash"
    "gemini-2.0-flash"
    "gemini-2.5-flash-preview-09-2025"
    "gemini-2.0-flash-live-001"
    "gemini-1.5-flash"
)

echo "Testing each model with Live API endpoint..."
echo ""

for model in "${models[@]}"; do
    echo "Testing: $model"
    
    # Test the Live API endpoint with a proper request
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
        -X POST "https://generativelanguage.googleapis.com/v1beta/models/${model}:bidiGenerateContent?key=${API_KEY}" \
        -H "Content-Type: application/json" \
        -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        -d '{"setup":{"model":"models/'${model}'"}}' 2>&1)
    
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    if [[ "$http_status" == "426" ]]; then
        echo "  ✅ Model supports Live API! (426 = Upgrade Required to WebSocket)"
    elif [[ "$http_status" == "404" ]]; then
        echo "  ❌ Model NOT FOUND"
    elif [[ "$http_status" == "400" ]]; then
        if [[ "$body" == *"policy"* ]] || [[ "$body" == *"violation"* ]]; then
            echo "  ❌ POLICY VIOLATION - Model doesn't support Live API"
        else
            echo "  ❌ BAD REQUEST - Model doesn't support Live API"
        fi
    elif [[ "$http_status" == "403" ]]; then
        echo "  ❌ FORBIDDEN - API key issue or paid tier required"
    else
        echo "  ⚠️  HTTP $http_status - $(echo "$body" | head -c 50)"
    fi
    
    sleep 0.5
done

echo ""
echo "======================================================================="
echo "RESULTS:"
echo "Models with ✅ support Live API (WebSocket required)"
echo "Models with ❌ don't support Live API or require paid tier"
echo "======================================================================="