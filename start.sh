#!/bin/bash
# Start DevKraft RAG Application (API + UI + Qdrant Docker management)

set -e

echo "======================================"
echo "DevKraft RAG Application Startup"
echo "======================================"

# Navigate to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠ Virtual environment not found. Using system Python."
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Docker and manage Qdrant containers
echo ""
echo "Checking for Qdrant Docker containers..."
if command_exists docker; then
    # Check for existing qdrant containers
    EXISTING_CONTAINERS=$(docker ps -a --filter "ancestor=qdrant/qdrant" --format "{{.ID}}" 2>/dev/null || true)
    
    if [ -n "$EXISTING_CONTAINERS" ]; then
        echo "✓ Found existing Qdrant container(s)"
        for CONTAINER_ID in $EXISTING_CONTAINERS; do
            CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_ID" 2>/dev/null || echo "unknown")
            echo "  Container $CONTAINER_ID status: $CONTAINER_STATUS"
            
            if [ "$CONTAINER_STATUS" = "exited" ] || [ "$CONTAINER_STATUS" = "created" ]; then
                echo "  → Starting container $CONTAINER_ID..."
                docker start "$CONTAINER_ID"
                echo "  ✓ Container started"
            elif [ "$CONTAINER_STATUS" = "running" ]; then
                echo "  ✓ Container already running"
            fi
        done
    else
        echo "⚠ No existing Qdrant containers found"
        echo "  To create one, run: docker run -d -p 6333:6333 qdrant/qdrant"
        echo "  The application will use Qdrant Cloud as fallback"
    fi
else
    echo "⚠ Docker not found. Qdrant Docker will not be available."
    echo "  The application will use Qdrant Cloud"
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p generate_embeddings/stored
mkdir -p generate_embeddings/stored_in_q_cloud_only
mkdir -p generate_embeddings/stored_in_q_docker_only
mkdir -p user_chat
echo "✓ Directories created"

# Check if required environment variables are set
echo ""
echo "Checking environment variables..."
ENV_VARS_OK=true
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠ GEMINI_API_KEY not set"
    ENV_VARS_OK=false
fi
if [ -z "$QDRANT_API_KEY" ]; then
    echo "⚠ QDRANT_API_KEY not set"
    ENV_VARS_OK=false
fi
if [ -z "$HF_TOKEN" ]; then
    echo "⚠ HF_TOKEN not set"
    ENV_VARS_OK=false
fi

if [ "$ENV_VARS_OK" = false ]; then
    echo ""
    echo "Please set the required environment variables or create a .env file"
    echo "See .env.example for reference"
fi

# Start FastAPI backend in the background
echo ""
echo "======================================"
echo "Starting FastAPI Backend..."
echo "======================================"
LOG_FILE="logs/uvicorn_$(date +%Y%m%d_%H%M%S).log"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &
API_PID=$!
echo "✓ FastAPI started (PID: $API_PID)"
echo "  Logs: $LOG_FILE"
echo "  URL: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"

# Wait for API to be ready
echo ""
echo "Waiting for API to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API is ready"
        break
    fi
    sleep 1
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo "  Still waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠ API did not become ready in time"
    echo "  Check logs at: $LOG_FILE"
fi

# Start Streamlit UI in the background
echo ""
echo "======================================"
echo "Starting Streamlit UI..."
echo "======================================"
STREAMLIT_LOG_FILE="logs/streamlit_$(date +%Y%m%d_%H%M%S).log"
streamlit run streamlit_app.py --server.port 8501 --server.headless true > "$STREAMLIT_LOG_FILE" 2>&1 &
UI_PID=$!
echo "✓ Streamlit started (PID: $UI_PID)"
echo "  Logs: $STREAMLIT_LOG_FILE"
echo "  URL: http://localhost:8501"

# Save PIDs to file for later cleanup
echo "$API_PID" > /tmp/devkraft_api.pid
echo "$UI_PID" > /tmp/devkraft_ui.pid

# Print summary
echo ""
echo "======================================"
echo "✓ DevKraft RAG is running!"
echo "======================================"
echo ""
echo "Services:"
echo "  • FastAPI Backend:  http://localhost:8000"
echo "  • API Docs:         http://localhost:8000/docs"
echo "  • Streamlit UI:     http://localhost:8501"
echo ""
echo "Logs:"
echo "  • FastAPI:          $LOG_FILE"
echo "  • Streamlit:        $STREAMLIT_LOG_FILE"
echo "  • Application:      logs/app_logs_$(date +%Y%m%d).log"
echo "  • Errors:           logs/errors_$(date +%Y%m%d).log"
echo ""
echo "Settings:"
echo "  • Configuration:    app/config.py"
echo ""
echo "To stop the application, run: ./stop.sh"
echo "Or manually kill processes: kill $API_PID $UI_PID"
echo ""
echo "Press Ctrl+C to stop monitoring (services will continue running)"
echo ""

# Monitor the processes
trap "echo ''; echo 'Monitoring stopped. Services still running.'; echo 'Run ./stop.sh to stop services.'; exit 0" INT

echo "Monitoring application logs (showing last 10 lines)..."
echo "======================================"
tail -f "$LOG_FILE" "$STREAMLIT_LOG_FILE" 2>/dev/null || {
    echo "Log monitoring stopped"
    echo ""
    echo "Services are still running in background"
    echo "Run ./stop.sh to stop them"
}
