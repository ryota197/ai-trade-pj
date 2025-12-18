#!/bin/bash
# API テストスクリプト
# 使用方法: ./scripts/test_api.sh

BASE_URL="http://localhost:8000/api"

echo "=== Quote API Test ==="
echo "GET /api/data/quote/AAPL"
curl -s "$BASE_URL/data/quote/AAPL" | python -m json.tool

echo ""
echo "=== History API Test ==="
echo "GET /api/data/history/AAPL?period=5d&interval=1d"
curl -s "$BASE_URL/data/history/AAPL?period=5d&interval=1d" | python -m json.tool

echo ""
echo "=== Invalid Symbol Test ==="
echo "GET /api/data/quote/INVALID123"
curl -s "$BASE_URL/data/quote/INVALID123" | python -m json.tool

echo ""
echo "=== Test Complete ==="
