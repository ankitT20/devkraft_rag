#!/bin/bash
# Start the FastAPI backend server

echo "Starting DevKraft RAG API Server..."
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start uvicorn server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
