#!/bin/bash
# Test script for Live Voice RAG endpoints

echo "======================================"
echo "Testing Live Voice RAG Backend APIs"
echo "======================================"
echo ""

# Base URL
BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s $BASE_URL/health | python3 -m json.tool
echo ""

# Test 2: Generate ephemeral token
echo "2. Testing token generation..."
TOKEN_RESPONSE=$(curl -s $BASE_URL/api/generate-token)
echo $TOKEN_RESPONSE | python3 -m json.tool
TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
echo "Generated token: ${TOKEN:0:50}..."
echo ""

# Test 3: Get function declarations
echo "3. Testing function declarations..."
curl -s $BASE_URL/api/function-declarations | python3 -m json.tool
echo ""

# Test 4: Search knowledge base
echo "4. Testing knowledge base search..."
curl -s -X POST $BASE_URL/api/search-knowledge-base \
  -H "Content-Type: application/json" \
  -d '{"query": "what is RAG", "top_k": 2}' | python3 -m json.tool
echo ""

# Test 5: Voice interface page
echo "5. Testing voice interface page..."
VOICE_PAGE=$(curl -s $BASE_URL/voice)
if [[ $VOICE_PAGE == *"Live Voice RAG"* ]]; then
    echo "✓ Voice interface page loads successfully"
else
    echo "✗ Voice interface page failed to load"
fi
echo ""

echo "======================================"
echo "All backend tests completed!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Open browser and navigate to: $BASE_URL/voice"
echo "2. Click 'Connect & Talk' button"
echo "3. Allow microphone access"
echo "4. Speak to test voice interaction"
echo "5. Ask questions about your documents"
echo ""
