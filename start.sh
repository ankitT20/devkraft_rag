#!/bin/bash
# Start DevKraft RAG Application

cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create necessary directories
mkdir -p logs generate_embeddings/stored generate_embeddings/stored_in_q_cloud_only generate_embeddings/stored_in_q_docker_only user_chat

# Check and start existing Qdrant Docker containers
if command -v docker >/dev/null 2>&1; then
    QDRANT_CONTAINERS=$(docker ps -a --filter "ancestor=qdrant/qdrant" --format "{{.ID}}" 2>/dev/null)
    if [ -n "$QDRANT_CONTAINERS" ]; then
        for CONTAINER_ID in $QDRANT_CONTAINERS; do
            STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_ID" 2>/dev/null)
            if [ "$STATUS" = "exited" ] || [ "$STATUS" = "created" ]; then
                docker start "$CONTAINER_ID" >/dev/null 2>&1
            fi
        done
    fi
fi

echo "Starting DevKraft RAG..."

# Start FastAPI backend
LOG_FILE="logs/uvicorn_$(date +%Y%m%d).log"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >> "$LOG_FILE" 2>&1 &
echo "FastAPI started at http://localhost:8000"

# Start Streamlit UI
STREAMLIT_LOG_FILE="logs/streamlit_$(date +%Y%m%d).log"
streamlit run streamlit_app.py --server.port 8501 --server.headless true >> "$STREAMLIT_LOG_FILE" 2>&1 &
echo "Streamlit UI started at http://localhost:8501"

echo ""
echo "Logs: $LOG_FILE and $STREAMLIT_LOG_FILE"
echo "To stop: pkill -f uvicorn; pkill -f streamlit"
