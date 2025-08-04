#!/bin/bash

echo "🚀 Starting Claude Code OpenAI Wrapper"

# Check Claude authentication
if ! claude auth whoami &> /dev/null; then
    echo "❌ Claude not authenticated. Please run: claude auth login"
    exit 1
fi

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start server
echo "🌐 Starting server on http://localhost:${PORT:-8000}"
python3 -m uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}
