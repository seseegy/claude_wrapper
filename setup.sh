#!/bin/bash

echo "🛠️ Claude Code OpenAI Wrapper Setup"
echo "=================================="

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Install Claude Code CLI
echo "📦 Installing Claude Code CLI..."
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file if needed"
fi

echo ""
echo "✅ Setup completed!"
echo ""
echo "🔐 Next steps:"
echo "1. Authenticate with Claude: claude auth login"
echo "2. Start the server: python3 -m uvicorn main:app --reload --port 8000"
echo "3. Test: python3 test_basic.py"
