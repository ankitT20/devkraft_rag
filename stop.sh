#!/bin/bash
# Stop DevKraft RAG Application

echo "======================================"
echo "Stopping DevKraft RAG Application"
echo "======================================"

# Function to stop process if running
stop_process() {
    local PID=$1
    local NAME=$2
    
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Stopping $NAME (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                echo "✓ $NAME stopped"
                return 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "  Force stopping $NAME..."
            kill -9 "$PID" 2>/dev/null || true
            echo "✓ $NAME stopped (forced)"
        fi
    else
        echo "⚠ $NAME not running (PID: $PID)"
    fi
}

# Stop FastAPI
if [ -f /tmp/devkraft_api.pid ]; then
    API_PID=$(cat /tmp/devkraft_api.pid)
    stop_process "$API_PID" "FastAPI Backend"
    rm -f /tmp/devkraft_api.pid
else
    echo "⚠ FastAPI PID file not found"
fi

# Stop Streamlit
if [ -f /tmp/devkraft_ui.pid ]; then
    UI_PID=$(cat /tmp/devkraft_ui.pid)
    stop_process "$UI_PID" "Streamlit UI"
    rm -f /tmp/devkraft_ui.pid
else
    echo "⚠ Streamlit PID file not found"
fi

# Also try to kill any remaining uvicorn/streamlit processes
echo ""
echo "Checking for any remaining processes..."
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✓ Stopped remaining uvicorn processes" || true
pkill -f "streamlit run streamlit_app.py" 2>/dev/null && echo "✓ Stopped remaining streamlit processes" || true

echo ""
echo "======================================"
echo "✓ DevKraft RAG stopped"
echo "======================================"
