# DevKraft RAG - Directory Structure and Architecture

## Overview

DevKraft RAG is a Retrieval-Augmented Generation (RAG) system with a Streamlit UI, FastAPI backend, and LangChain integration. It supports dual model options (Gemini Cloud and Local LMStudio/HF), dual vector storage (Qdrant Cloud and Docker), and MongoDB Atlas for chat history.

---

## Directory Structure

```
devkraft_rag/
├── app/                              # Main application package
│   ├── core/                         # Core functionality modules
│   │   ├── __init__.py              # Package initializer
│   │   ├── chat_storage.py          # MongoDB Atlas chat history with JSON fallback
│   │   ├── embeddings.py            # Embedding services (Gemini & Local/HF)
│   │   ├── llm.py                   # LLM services (Gemini & Local/HF)
│   │   ├── storage.py               # Qdrant vector storage (Cloud & Docker)
│   │   └── tts.py                   # Text-to-Speech service (Gemini TTS)
│   │
│   ├── models/                       # Pydantic data models
│   │   ├── __init__.py              # Package initializer
│   │   └── schemas.py               # Request/Response schemas
│   │
│   ├── services/                     # Business logic services
│   │   ├── __init__.py              # Package initializer
│   │   ├── document_processor.py    # Document loading and chunking
│   │   ├── ingestion.py             # Document ingestion pipeline
│   │   └── rag.py                   # RAG query processing
│   │
│   ├── utils/                        # Utility modules
│   │   ├── __init__.py              # Package initializer
│   │   └── logging_config.py        # Logging configuration
│   │
│   ├── __init__.py                   # App package initializer
│   ├── config.py                     # Configuration management
│   └── main.py                       # FastAPI application
│
├── info/                             # Documentation folder
│   ├── info.md                       # This file - Directory structure info
│   └── deep-dive.puml               # Detailed PlantUML diagram
│
├── generate_embeddings/              # Document upload folder (runtime)
├── user_chat/                        # Chat history storage (runtime)
├── logs/                             # Application logs (runtime)
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
├── start.sh                          # Startup script
└── streamlit_app.py                 # Streamlit UI application
```

---

## File Relationships and Responsibilities

### 1. **Entry Points**
- **`streamlit_app.py`**: User-facing Streamlit UI for chatbot interaction
- **`app/main.py`**: FastAPI backend providing REST API endpoints
- **`start.sh`**: Shell script to start services

### 2. **Configuration Layer**
- **`app/config.py`**: Centralized configuration using Pydantic Settings
  - Loads environment variables (.env file)
  - Defines API keys, URLs, model names, paths
  - Used by all modules for configuration

### 3. **Core Services Layer**

#### **`app/core/embeddings.py`**
- **GeminiEmbedding**: Cloud embedding service using Gemini API
  - 3072-dimensional vectors
  - Rate-limited API calls (10s delay every 50 calls)
  - Methods: `embed_documents()`, `embed_query()`
  
- **LocalEmbedding**: Local embedding with HF fallback
  - 768-dimensional vectors
  - LM Studio primary, HuggingFace fallback
  - Normalizes embeddings to unit length
  - Methods: `embed_documents()`, `embed_query()`

#### **`app/core/storage.py`**
- **QdrantStorage**: Vector database management
  - Manages Qdrant Cloud and Docker collections
  - Collections: `bootcamp_rag_cloud` (3072d), `bootcamp_rag_docker` (768d)
  - Methods:
    - `store_embeddings_cloud()`: Store in cloud collection
    - `store_embeddings_docker()`: Store in docker with cloud replication
    - `search_cloud()`: Search cloud collection
    - `search_docker()`: Search docker with cloud fallback
    - `check_document_exists()`: Prevent duplicate ingestion

#### **`app/core/llm.py`**
- **GeminiLLM**: Cloud LLM service using Gemini API
  - Model: gemini-2.5-flash
  - Supports streaming responses
  - Methods: `generate_response_with_sources()`, `generate_response_with_sources_stream()`
  
- **LocalLLM**: Local LLM with HF fallback
  - Model: qwen3-1.7b
  - Supports thinking blocks
  - LM Studio primary, HuggingFace fallback
  - Methods: `generate_response_with_sources()`

#### **`app/core/chat_storage.py`**
- **ChatStorageService**: Chat history management
  - MongoDB Atlas primary storage
  - JSON file fallback if MongoDB unavailable
  - Methods:
    - `save_chat_history()`: Save chat session
    - `load_chat_history()`: Load chat session
    - `get_recent_chats()`: List recent chats
    - `get_chat_history()`: Get full chat details

#### **`app/core/tts.py`**
- **TTSService**: Text-to-Speech conversion
  - Uses Gemini TTS API (gemini-2.5-flash-preview-tts)
  - Converts text to WAV audio
  - Methods: `text_to_speech()`

### 4. **Service Layer**

#### **`app/services/document_processor.py`**
- **DocumentProcessor**: Document loading and chunking
  - Supports: TXT, PDF, DOCX, MD formats
  - Uses LangChain loaders and RecursiveCharacterTextSplitter
  - Chunk size: 2000 chars, overlap: 400 chars
  - Preserves page numbers and headers for PDFs
  - Methods:
    - `load_document()`: Load and chunk document
    - `_process_pdf_with_metadata()`: PDF-specific processing
    - `calculate_md5()`: Calculate file hash

#### **`app/services/ingestion.py`**
- **IngestionService**: Document ingestion pipeline
  - Orchestrates embedding generation and storage
  - Handles both Gemini and Local embeddings
  - Stores in both cloud and docker collections
  - Moves processed files to appropriate folders
  - Methods:
    - `ingest_document()`: Ingest single document
    - `ingest_all_documents()`: Batch ingestion

#### **`app/services/rag.py`**
- **RAGService**: Query processing and response generation
  - Orchestrates the full RAG pipeline
  - Manages chat history
  - Retrieves context from vector store
  - Generates responses with source tracking
  - Methods:
    - `query()`: Process user query
    - `query_stream()`: Streaming query processing (Gemini only)
    - `get_recent_chats()`: Get chat list
    - `get_chat_history()`: Get chat details

### 5. **Models Layer**

#### **`app/models/schemas.py`**
- Pydantic models for request/response validation:
  - **QueryRequest**: User query input
  - **QueryResponse**: Generated response with sources
  - **SourceInfo**: Source document information
  - **IngestionResponse**: Document upload status
  - **ChatHistoryItem**: Chat session metadata
  - **HealthResponse**: Health check status

### 6. **Utilities Layer**

#### **`app/utils/logging_config.py`**
- Centralized logging configuration
  - Separate logs: `app_logs_{date}.log`, `errors_{date}.log`
  - File and console handlers
  - Exports: `app_logger`, `error_logger`

---

## Data Flow Diagrams

### PlantUML Architecture Diagram

This diagram shows the high-level architecture and relationships between all files.

**Rendered Image**: See `DevKraft_RAG_Architecture.png` in this folder for the visual diagram.

**PlantUML Source Code**: See `architecture-simple.puml` for the source code.

**Key Components**:
- **Entry Points** (Green): User interfaces and startup scripts
- **Configuration** (Yellow): Settings and environment management
- **Core Services** (Blue): Embedding, LLM, storage, and TTS services
- **Business Services** (Purple): Document processing and RAG orchestration
- **Data Models** (Pink): Request/response validation schemas
- **Utilities** (Brown): Logging infrastructure
- **External Services** (Orange): Third-party APIs and databases
- **Runtime Folders** (Gray): Dynamic data storage

---

## Explanation of Architecture

### Request Flow

#### 1. **Document Ingestion Flow**
```
User (UI) 
  → FastAPI /upload endpoint 
  → IngestionService 
  → DocumentProcessor (load & chunk) 
  → GeminiEmbedding/LocalEmbedding (generate embeddings) 
  → QdrantStorage (store vectors) 
  → Move file to storage folder
```

#### 2. **Query Processing Flow (RAG)**
```
User (UI) 
  → FastAPI /query endpoint 
  → RAGService 
  → Load chat history (ChatStorageService) 
  → Generate query embedding (GeminiEmbedding/LocalEmbedding) 
  → Search vectors (QdrantStorage) 
  → Generate response (GeminiLLM/LocalLLM) 
  → Extract sources 
  → Save chat history 
  → Return response with sources
```

#### 3. **Chat History Flow**
```
User (UI) 
  → FastAPI /chats endpoint 
  → RAGService 
  → ChatStorageService 
  → MongoDB Atlas (primary) or JSON files (fallback) 
  → Return chat list
```

### Key Design Patterns

1. **Dual Provider Pattern**: 
   - Embeddings: Gemini Cloud (3072d) vs Local/HF (768d)
   - LLM: Gemini (gemini-2.5-flash) vs Local/HF (qwen3-1.7b)
   - Storage: Qdrant Cloud vs Qdrant Docker
   - Chat: MongoDB Atlas vs JSON files

2. **Fallback Strategy**:
   - Local embeddings/LLM try LM Studio first, fall back to HuggingFace
   - Qdrant Docker searches try local first, fall back to cloud
   - Chat storage tries MongoDB first, falls back to JSON files

3. **Service Layer Architecture**:
   - Core services (embeddings, llm, storage) are independent and reusable
   - Business services (RAG, Ingestion) orchestrate core services
   - Clear separation of concerns

4. **Configuration-Driven**:
   - All settings centralized in `config.py`
   - Environment variable based configuration
   - Easy to modify without code changes

5. **Source Tracking**:
   - LLMs indicate which documents they used
   - Sources extracted and returned to user
   - Includes page, header, filename, chunk info

6. **Rate Limiting**:
   - Gemini embedding API: 10-second delay every 50 calls
   - Prevents quota exhaustion

7. **Document Deduplication**:
   - MD5 hash-based check before ingestion
   - Prevents duplicate document storage

---

## Module Dependencies

### Dependency Graph
```
streamlit_app.py → app/main.py (FastAPI)

app/main.py → 
  ├── app/services/rag.py
  ├── app/services/ingestion.py
  ├── app/core/tts.py
  ├── app/models/schemas.py
  └── app/utils/logging_config.py

app/services/rag.py → 
  ├── app/core/embeddings.py (GeminiEmbedding, LocalEmbedding)
  ├── app/core/llm.py (GeminiLLM, LocalLLM)
  ├── app/core/storage.py (QdrantStorage)
  ├── app/core/chat_storage.py (ChatStorageService)
  ├── app/config.py
  └── app/utils/logging_config.py

app/services/ingestion.py → 
  ├── app/services/document_processor.py
  ├── app/core/embeddings.py (GeminiEmbedding, LocalEmbedding)
  ├── app/core/storage.py (QdrantStorage)
  ├── app/config.py
  └── app/utils/logging_config.py

app/services/document_processor.py → 
  ├── app/config.py
  ├── app/utils/logging_config.py
  └── langchain libraries

app/core/embeddings.py → 
  ├── app/config.py
  ├── app/utils/logging_config.py
  ├── google.genai (Gemini)
  └── huggingface_hub (HF)

app/core/llm.py → 
  ├── app/config.py
  ├── app/utils/logging_config.py
  ├── google.genai (Gemini)
  └── huggingface_hub (HF)

app/core/storage.py → 
  ├── app/config.py
  ├── app/utils/logging_config.py
  └── qdrant_client

app/core/chat_storage.py → 
  ├── app/config.py
  ├── app/utils/logging_config.py
  └── pymongo

app/core/tts.py → 
  ├── app/config.py
  ├── app/utils/logging_config.py
  └── google.genai (Gemini)

app/config.py → 
  ├── pydantic
  └── .env file

app/utils/logging_config.py → 
  └── logging (stdlib)
```

---

## Technology Stack

### Backend
- **FastAPI**: REST API framework
- **Pydantic**: Data validation
- **LangChain**: Document loading and chunking
- **Qdrant**: Vector database
- **MongoDB**: Chat history database
- **Google Gemini**: Cloud LLM and embeddings
- **LM Studio**: Local LLM inference
- **HuggingFace**: Fallback LLM and embeddings

### Frontend
- **Streamlit**: Web UI framework

### Development
- **Python 3.x**: Programming language
- **uvicorn**: ASGI server

---

## Configuration

Key configuration parameters (from `app/config.py`):

```python
# API Keys
- GEMINI_API_KEY
- QDRANT_API_KEY
- HF_TOKEN
- MONGO_URI

# Model Configuration
- gemini_embedding_model: "gemini-embedding-001"
- gemini_chat_model: "gemini-2.5-flash"
- local_embedding_model: "text-embedding-embeddinggemma-300m-qat"
- local_chat_model: "qwen/qwen3-1.7b"

# Storage
- qdrant_cloud_url: Qdrant Cloud endpoint
- qdrant_docker_url: "http://localhost:6333"
- mongo_uri: MongoDB Atlas connection string

# Chunking
- chunk_size: 2000 characters
- chunk_overlap: 400 characters

# Paths
- generate_embeddings_folder: Document upload location
- user_chat_folder: Chat history storage
- logs_folder: Application logs
```

---

## How Components Work Together

### Example: Processing a User Query

1. **User submits query** via Streamlit UI
2. **Streamlit** sends HTTP POST to `/query` endpoint
3. **FastAPI** receives request, validates with Pydantic schemas
4. **RAGService.query()** is called:
   - Loads chat history from **ChatStorageService** (MongoDB/JSON)
   - Generates query embedding via **GeminiEmbedding** or **LocalEmbedding**
   - Searches vectors in **QdrantStorage** (Cloud or Docker)
   - Builds context from top 4 results
   - Generates response via **GeminiLLM** or **LocalLLM**
   - Extracts which sources were used
   - Updates chat history via **ChatStorageService**
   - Returns response with sources
5. **FastAPI** returns JSON response
6. **Streamlit** displays response to user

### Example: Ingesting a Document

1. **User uploads document** via Streamlit UI
2. **Streamlit** sends HTTP POST to `/upload` endpoint
3. **FastAPI** saves file temporarily
4. **IngestionService.ingest_document()** is called:
   - **DocumentProcessor** loads and chunks document
   - Calculates MD5 hash
   - **QdrantStorage** checks if document exists
   - **GeminiEmbedding** generates embeddings (3072d)
   - **QdrantStorage** stores in cloud collection
   - **LocalEmbedding** generates embeddings (768d)
   - **QdrantStorage** stores in docker collection (with cloud replication)
   - Moves file to appropriate storage folder
5. **FastAPI** returns success status
6. **Streamlit** shows confirmation to user

---

## Logging Strategy

The application uses a dual-logging approach:

1. **App Logs** (`logs/app_logs_{date}.log`):
   - INFO level and above
   - All normal operations
   - Performance metrics
   - API calls

2. **Error Logs** (`logs/errors_{date}.log`):
   - ERROR level only
   - Exceptions and failures
   - Detailed error traces

Both logs include:
- Timestamp
- Module name
- Log level
- Function name and line number
- Message

---

## Summary

The DevKraft RAG application is a well-architected system with:

- **Clear separation of concerns**: Entry points, configuration, core services, business services, models, and utilities
- **Dual provider support**: Cloud (Gemini) and Local (LM Studio/HF) for flexibility
- **Robust fallback mechanisms**: Ensures availability even when services are down
- **Source tracking**: Provides transparency in RAG responses
- **Comprehensive logging**: Aids in debugging and monitoring
- **Flexible storage**: Supports multiple vector stores and chat history backends
- **Modular design**: Easy to extend and maintain

Each file has a specific responsibility, and the relationships between files follow a clear architectural pattern, making the codebase maintainable and scalable.

---

## Generated Diagrams

This documentation includes comprehensive PlantUML diagrams that have been rendered as PNG images:

### 1. Architecture Overview (`DevKraft_RAG_Architecture.png`)
- **Size**: ~204 KB
- **Description**: High-level architecture showing all major components and their relationships
- **Source**: `architecture-simple.puml`
- **Shows**:
  - Entry points (Streamlit UI, FastAPI, startup script)
  - Configuration layer
  - Core services (embeddings, LLM, storage)
  - Business services (RAG, ingestion, document processing)
  - External dependencies (Gemini API, LM Studio, HuggingFace, Qdrant, MongoDB)
  - Runtime folders

### 2. Deep Dive Diagram (`DevKraft_RAG_Deep_Dive.png`)
- **Size**: ~1.5 MB
- **Description**: Comprehensive diagram showing every class, method, and function
- **Source**: `deep-dive.puml`
- **Shows**:
  - All classes with their attributes and methods
  - Public and private methods
  - Method signatures with parameters and return types
  - Detailed relationships and dependencies
  - Notes on implementation details
  - Complete function hierarchy

### How to View the Diagrams

1. **In this folder**: Open the PNG files directly
   - `DevKraft_RAG_Architecture.png` - High-level overview
   - `DevKraft_RAG_Deep_Dive.png` - Detailed view

2. **Edit the diagrams**: Modify the `.puml` files and regenerate with:
   ```bash
   # Install PlantUML (requires Java)
   wget https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar
   
   # Generate PNG
   java -jar plantuml.jar -tpng architecture-simple.puml
   java -jar plantuml.jar -tpng deep-dive.puml
   ```

3. **Online viewer**: Copy the PlantUML code to http://www.plantuml.com/plantuml/ for live editing

### Diagram Legend

Both diagrams use color coding to distinguish component types:

| Color | Component Type | Description |
|-------|---------------|-------------|
| Light Green (#E8F5E9) | Entry Points | User interfaces and startup scripts |
| Light Yellow (#FFF9C4) | Configuration | Settings and environment management |
| Light Blue (#E3F2FD) | Core Services | Embedding, LLM, storage services |
| Light Purple (#F3E5F5) | Business Services | RAG and ingestion orchestration |
| Light Pink (#FCE4EC) | Data Models | Pydantic schemas |
| Light Brown (#EFEBE9) | Utilities | Logging and helpers |
| Light Orange (#FFE0B2) | External Services | Third-party APIs |
| Gray (#E0E0E0) | Runtime Folders | Dynamic data storage |

---

## Files in This Folder

- **`info.md`** (this file): Complete directory structure documentation and architecture explanation
- **`deep-dive.puml`**: PlantUML source for the comprehensive deep-dive diagram
- **`architecture-simple.puml`**: PlantUML source for the high-level architecture diagram
- **`DevKraft_RAG_Architecture.png`**: Rendered high-level architecture diagram (204 KB)
- **`DevKraft_RAG_Deep_Dive.png`**: Rendered deep-dive diagram with all functions (1.5 MB)
