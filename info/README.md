# Info Folder

This folder contains documentation, API collections, and configuration templates for the DevKraft RAG system.

## Contents

### 📮 Postman Collection Files

#### `rag.postman_collection.json`
Complete Postman collection with all API endpoints. Includes:

- **Health Check Endpoints**
  - `GET /` - Root health check
  - `GET /health` - Detailed health status

- **Query Endpoints**
  - `POST /query` - RAG query with Gemini model
  - `POST /query` - RAG query with Qwen3 local model
  - `POST /query` - RAG query with chat history continuation
  - `POST /query-stream` - Streaming RAG query (Gemini)
  - `POST /query-stream` - Streaming RAG query (Qwen3)

- **Document Management**
  - `POST /upload` - Upload and ingest a document
  - `POST /ingest-all` - Bulk ingest all documents

- **Chat History**
  - `GET /chats?limit=10` - Get recent chat sessions
  - `GET /chat/{chat_id}` - Get full chat history

- **Text to Speech**
  - `POST /tts` - Convert text to audio (WAV)

**Usage:**
1. Open Postman
2. Import `rag.postman_collection.json`
3. All requests are pre-filled with example data
4. Update the `base_url` variable if needed (default: `http://localhost:8000`)

#### `rag.postman_environment.json`
Environment variables for the Postman collection:
Currently API Keys are managed by app\config.py, no need to put in Postman

- `base_url` - API base URL (default: `http://localhost:8000`)
- `gemini_api_key` - Gemini API key (replace `****` with actual key)
- `qdrant_api_key` - Qdrant API key (replace `****` with actual key)
- `hf_token` - HuggingFace token (replace `****` with actual key)
- `mongo_uri` - MongoDB connection string (replace `****` with actual URI)
- `qdrant_cloud_url` - Qdrant Cloud URL
- `qdrant_docker_url` - Qdrant Docker URL
- `lmstudio_url` - LM Studio URL
- `qdrant_cloud_collection` - Cloud collection name
- `qdrant_docker_collection` - Docker collection name

**Usage:**
1. Import `rag.postman_environment.json` into Postman
2. Select "DevKraft RAG Environment" from the environment dropdown
3. Replace all `****` placeholders with your actual API keys
4. Save the environment

### ⚙️ Configuration Template

#### `.env.example`
Template for environment variables. Copy this file to the project root as `.env` and fill in your actual values:

```bash
# Copy this file to the project root and rename to .env
cp info/.env.example ../.env

# Then edit the .env file with your actual API keys
```

Required variables:
- `GEMINI_API_KEY` - Google Gemini API key
- `QDRANT_API_KEY` - Qdrant Cloud API key
- `HF_TOKEN` - HuggingFace API token
- `MONGO_URI` - MongoDB Atlas connection string

### 🏗️ Architecture Diagram

#### `architecture-simple.puml`
PlantUML diagram showing the complete system architecture.

**Components:**
- Entry Points (Streamlit UI, FastAPI, startup script)
- Configuration management
- Core Services (embeddings, LLM, storage, TTS)
- Business Services (RAG, ingestion, document processing)
- External integrations (Gemini, Qdrant, MongoDB, HuggingFace, LM Studio)
- Runtime folders (documents, chat history, logs)

**View the diagram:**
- Use PlantUML viewer/extension in your IDE
- Online: Copy content to http://www.plantuml.com/plantuml/uml/
- VS Code: Install PlantUML extension

## Quick Start

1. **Set up environment:**
   ```bash
   cp info/.env.example .env
   # Edit .env with your API keys
   ```

2. **Import Postman files:**
   - Import `rag.postman_collection.json`
   - Import `rag.postman_environment.json`
   - Update environment variables with actual keys

3. **Start testing:**
   - Start the FastAPI server: `uvicorn app.main:app --reload`
   - Open Postman and start making requests

## Notes

- All Postman requests have pre-filled example data
- The environment file uses `****` as placeholders for security
- Never commit actual API keys to the repository
- The architecture diagram provides a comprehensive overview of the system
