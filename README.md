# DevKraft RAG Application

A simple Retrieval-Augmented Generation (RAG) system with a Streamlit UI, FastAPI backend, and LangChain integration.

## Features

- 🤖 **Dual Model Support**: Choose between Gemini Cloud (gemini-2.5-flash) or Local LMStudio/HF (qwen3-1.7b)
- 🎤 **Live Voice RAG**: Real-time voice interaction with native audio (Gemini 2.5 Flash Native Audio)
  - Real-time speech transcription for user speech (Web Speech API)
  - Live audio responses from AI assistant
  - Visual transcript showing conversation flow
  - RAG function calling for knowledge base search
- 📚 **Document Ingestion**: Upload and process multiple document types (TXT, PDF, DOCX, MD)
- 💾 **Vector Storage**: Dual storage with Qdrant Cloud and Docker
- 💬 **Chat History**: Persistent chat sessions stored in MongoDB Atlas (with JSON file fallback)
- 🧠 **Thinking Display**: View model reasoning process (qwen3)
- 🔍 **RAG Pipeline**: Semantic search and context-aware responses
- 🔊 **Text-to-Speech**: Convert text responses to audio using Gemini TTS

## Project Structure

```
devkraft_rag/
├── app/
│   ├── core/              # Core functionality
│   │   ├── embeddings.py  # Embedding services (Gemini, Local/HF)
│   │   ├── llm.py         # LLM services (Gemini, Local/HF)
│   │   ├── storage.py     # Qdrant vector storage
│   │   ├── chat_storage.py # MongoDB chat history storage
│   │   ├── tts.py         # Text-to-speech service
│   │   └── live_api.py    # Live API ephemeral token service
│   ├── services/          # Business logic
│   │   ├── document_processor.py  # Document loading and chunking
│   │   ├── ingestion.py   # Document ingestion pipeline
│   │   └── rag.py         # RAG query processing
│   ├── models/            # Pydantic schemas
│   │   └── schemas.py
│   ├── utils/             # Utilities
│   │   └── logging_config.py
│   ├── config.py          # Configuration
│   └── main.py            # FastAPI application
├── info/                  # Documentation and API collections
│   ├── rag.postman_collection.json  # Postman API collection
│   ├── rag.postman_environment.json # Postman environment file
│   ├── .env.example       # Environment variable template
│   ├── architecture-simple.puml     # System architecture diagram
│   └── DevKraft_RAG_Architecture.png # Architecture diagram image
├── static/                # Live Voice RAG frontend
│   ├── voice.html         # Voice interface page
│   ├── voice.js           # JavaScript client using @google/genai SDK
│   ├── voice.css          # Voice interface styling
│   └── package.json       # Optional: NPM config for local SDK installation
├── streamlit_app.py       # Streamlit UI
├── generate_embeddings/   # Document upload folder
├── user_chat/             # Chat history storage
├── logs/                  # Application logs
└── requirements.txt       # Dependencies
```
![RAG Architecture](info/DevKraft_RAG_Architecture.png)

## Setup

### 1. Environment Variables

Set the following environment variables:

```bash
export GEMINI_API_KEY="your_gemini_api_key"
export QDRANT_API_KEY="your_qdrant_api_key"
export HF_TOKEN="your_huggingface_token"
export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true"
```

Or create a `.env` file (see `info/.env.example`).

**MongoDB Atlas Setup (Optional):**
- If `MONGO_URI` is provided, chat history will be stored in MongoDB Atlas
- The application automatically appends `&w=majority&appName=ragcluster` to the URI
- If MongoDB is unavailable or not configured, the app falls back to JSON files in `user_chat/`
- No code changes needed - fallback is automatic

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Optional: Start Qdrant Docker

The application will automatically check for existing Qdrant Docker containers and resume them. If no containers exist, you can create one:

```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

The application will fall back to Qdrant Cloud if Docker is not available.

## Running the Application

### Quick Start (Recommended)

Use the provided startup script to start both API and UI:

```bash
./start.sh
```

This will automatically:
- Check for and resume existing Qdrant Docker containers (if any)
- Start the FastAPI backend on port 8000
- Start the Streamlit UI on port 8501
- Append logs to `logs/uvicorn_YYYYMMDD.log` and `logs/streamlit_YYYYMMDD.log`

To stop the application:

```bash
pkill -f uvicorn
pkill -f streamlit
```

### Manual Start

Alternatively, you can start services manually:

**Terminal 1 - FastAPI Backend:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Streamlit UI:**
```bash
streamlit run streamlit_app.py
```

### Access Points

- **Streamlit UI**: http://localhost:8501 (Port: 8501)
- **FastAPI Backend**: http://localhost:8000 (Port: 8000)
- **API Documentation**: http://localhost:8000/docs
- **Live Voice RAG**: http://localhost:8000/voice (Native audio interface)

## Usage

### Model Selection

Choose between two models in the sidebar dropdown:

1. **Gemini Cloud** (Default):
   - Embedding: gemini-embedding-001 (3072 dimensions)
   - LLM: gemini-2.5-flash
   - Storage: Qdrant Cloud

2. **Qwen3 Local**:
   - Embedding: embeddinggemma-300m (768 dimensions) with HF fallback
   - LLM: qwen/qwen3-1.7b with HF fallback
   - Storage: Qdrant Docker with Cloud replication

### Upload Documents

1. Click "Upload Document" in sidebar
2. Select a file (TXT, PDF, DOCX, MD, or CSV)
3. Click "Upload" button
4. Document will be processed and stored in vector databases

You can also ingest website content using the `/ingest-website` API endpoint

### Chat

1. Type your question in the chat input
2. Press Enter to send
3. View the AI response
4. For Qwen3 model, expand "Show Thinking" to see reasoning

### Chat History

- Recent chats appear in the sidebar
- Click a chat to load it
- Click "New Chat" to start fresh

### Live Voice RAG

Access the Live Voice RAG interface at http://localhost:8000/voice for real-time voice interaction:

1. **Click "Start Conversation"** to begin
2. **Speak naturally** into your microphone
3. **AI responds with voice** in real-time
4. **RAG Integration**: The AI can search your knowledge base during conversation
5. **View transcript** to see the conversation flow

**Technical Details:**
- Uses Gemini 2.5 Flash Native Audio model for low-latency audio
- Ephemeral token authentication (30-minute expiry, single-use tokens)
- Client-to-Gemini direct connection (no backend audio proxy)
- Automatic Voice Activity Detection (VAD) for interruption handling
- Function calling for RAG knowledge base search

**Frontend Implementation:**
- JavaScript SDK (`@google/genai`) loaded from CDN by default
- Optional local installation available (see `static/package.json`)
- Pure ES6 modules, no build step required
- Real-time audio streaming with Web Audio API

## API Endpoints

### Standard API Endpoints

- `GET /` - Health check
- `GET /health` - Health status
- `POST /query` - Process RAG query
- `POST /query-stream` - Process RAG query with streaming response
- `POST /upload` - Upload and ingest document (supports TXT, PDF, DOCX, MD, CSV)
- `POST /ingest-all` - Ingest all documents in folder
- `POST /ingest-website` - Ingest content from a website URL
- `GET /chats` - Get recent chat sessions
- `GET /chat/{chat_id}` - Get full chat history
- `POST /tts` - Convert text to speech

### Live API Endpoints (Voice Interface)

- `GET /voice` - Access Live Voice RAG interface
- `GET /api/generate-token` - Generate ephemeral token for client-side Live API access
- `GET /api/function-declarations` - Get RAG function declarations for Live API
- `POST /api/search-knowledge-base` - Search knowledge base (called by Live API as tool function)

Visit http://localhost:8000/docs for interactive API documentation.

### Testing with Postman

A complete Postman collection is available in the `info/` folder:

1. **Collection**: `info/rag.postman_collection.json` - Contains all API endpoints with pre-filled examples
2. **Environment**: `info/rag.postman_environment.json` - Environment variables for API keys and configuration (Currently API Keys are managed by app\config.py, no need to put in Postman)

To use:
1. Import both files into Postman
2. Update the environment variables with your actual API keys (replace `****`)
3. Start testing the APIs immediately

## Configuration

All application settings are centralized in `app/config.py`. You can customize:

- API keys and tokens (via environment variables or .env file)
- MongoDB connection URI for chat history storage
- Chunk size and overlap for document processing
- Model names for embeddings and LLM
- Qdrant URLs and collection names
- File paths and directories
- LM Studio configuration

See `app/config.py` for all available settings.

### Chat History Storage

The application uses a dual-storage strategy for chat history:

1. **Primary Storage**: MongoDB Atlas (when `MONGO_URI` is configured)
   - Persistent cloud storage
   - Better query performance for large chat histories
   - Automatic indexing on `chat_id` and `updated_at`

2. **Fallback Storage**: JSON files in `user_chat/` folder
   - Activated when MongoDB is unavailable or not configured
   - Zero-configuration required
   - Compatible with existing chat history files

The application automatically handles the fallback logic. You don't need to modify any code.

## Logging

All logs are stored in the `logs/` folder with automatic date-based naming:

- `app_logs_YYYYMMDD.log` - All application logs (INFO level and above)
- `errors_YYYYMMDD.log` - Error logs only (ERROR level)
- `uvicorn_YYYYMMDD.log` - FastAPI/Uvicorn server logs (appended daily)
- `streamlit_YYYYMMDD.log` - Streamlit UI logs (appended daily)

Logs are appended when the application is restarted multiple times on the same day. Logs include detailed timestamps, function names, and line numbers for debugging.

## Embedding Details

### Gemini (Cloud)
- **Model**: gemini-embedding-001
- **Dimensions**: 3072
- **Normalization**: Pre-normalized by API
- **Task Type**: RETRIEVAL_DOCUMENT for docs, RETRIEVAL_QUERY for queries

### Local (LMStudio/HF)
- **Model**: embeddinggemma-300m
- **Dimensions**: 768
- **Normalization**: Manual normalization required
- **Fallback**: HuggingFace API if LMStudio unavailable

## Document Processing

### Chunking Strategy
- **Method**: RecursiveCharacterTextSplitter with LangChain
- **Chunk Size**: 1500 characters
- **Overlap**: 300 characters
- **Note**: Semantic chunking is available but disabled by default to avoid consuming API quota

### Supported Formats
- **Documents**: TXT, PDF, DOCX, MD, CSV
- **Web**: Websites via URL (using LangChain WebBaseLoader)

## Storage Strategy

Documents are processed and stored in both:
1. **Qdrant Cloud** with Gemini embeddings (3072d)
2. **Qdrant Docker** with Local embeddings (768d)

After processing, files are moved to:
- `generate_embeddings/stored/` - Both storages succeeded
- `generate_embeddings/stored_in_q_cloud_only/` - Cloud only
- `generate_embeddings/stored_in_q_docker_only/` - Docker only

### Make By Ankit Tayal
