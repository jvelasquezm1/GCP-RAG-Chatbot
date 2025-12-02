#!/bin/bash
# Simple health check test script

echo "Testing backend health endpoint..."
echo ""

# Test if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running!"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "❌ Backend is not running. Start it with:"
    echo "   cd backend && uvicorn app.main:app --reload --port 8000"
fi


