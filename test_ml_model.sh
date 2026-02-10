#!/bin/bash

# Test script for ML model endpoints

echo "Testing ML Model Integration"
echo "=============================="
echo ""

# Set the base URL (change for production)
BASE_URL="${1:-http://localhost:8000}"

echo "Using base URL: $BASE_URL"
echo ""

# Test 1: Check model info
echo "1. Checking model info..."
curl -s "$BASE_URL/model/info" | python3 -m json.tool
echo ""
echo ""

# Test 2: Health check
echo "2. Checking health (includes model status)..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test 3: Positive sentiment
echo "3. Testing positive sentiment..."
curl -s -X POST "$BASE_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is absolutely amazing! Best purchase ever!"}' \
  | python3 -m json.tool
echo ""
echo ""

# Test 4: Negative sentiment
echo "4. Testing negative sentiment..."
curl -s -X POST "$BASE_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "Terrible quality, completely disappointed and frustrated"}' \
  | python3 -m json.tool
echo ""
echo ""

# Test 5: Neutral text
echo "5. Testing neutral text..."
curl -s -X POST "$BASE_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "The package arrived on schedule"}' \
  | python3 -m json.tool
echo ""
echo ""

# Test 6: Multiple predictions
echo "6. Testing multiple predictions..."
for text in \
  "Love it!" \
  "Hate it!" \
  "It works" \
  "Excellent service" \
  "Poor experience"
do
  echo "  Text: '$text'"
  curl -s -X POST "$BASE_URL/predict" \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$text\"}" \
    | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"    -> {data['sentiment']} (confidence: {data['confidence']:.2f})\")"
done

echo ""
echo "=============================="
echo "Testing complete!"
