#!/bin/bash

# Contract Intelligence System - API Startup Script

echo "======================================================================"
echo "  Contract Intelligence System - Starting API Server"
echo "======================================================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your OPENAI_API_KEY"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if grep -q "OPENAI_API_KEY=your_" .env; then
    echo "❌ Error: OPENAI_API_KEY not configured in .env"
    echo "Please update .env with your actual OpenAI API key"
    exit 1
fi

echo "✓ Environment configured"
echo ""

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

echo "✓ Dependencies ready"
echo ""

# Start the API server
echo "🚀 Starting FastAPI server..."
echo ""
echo "  Local:    http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Health:   http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================================"
echo ""

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload