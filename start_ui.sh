#!/bin/bash
# Start the Streamlit UI

echo "Starting DevKraft RAG Streamlit UI..."
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start streamlit
streamlit run streamlit_app.py --server.port 8501 --server.headless true
