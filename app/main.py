"""
FastAPI application for RAG system.

Render Deployment - Single Service:
    Start Command: python -m app.main
    Environment Variables:
        - PORT: Set by Render automatically
        - START_STREAMLIT: Set to "true" to auto-start Streamlit (default: true)
    
    This deployment:
    - Starts FastAPI on $PORT (main process)
    - Auto-starts Streamlit on internal port 8501 (subprocess)
    - Root URL (/) redirects to Streamlit UI at /app
    - API endpoints remain accessible at /query, /upload, /health, etc.
    - Streamlit is proxied through FastAPI at /app route
    
    Access:
    - Visit https://your-app.onrender.com/ -> Redirects to Streamlit
    - Streamlit UI: https://your-app.onrender.com/app
    - API endpoints: https://your-app.onrender.com/query, /health, etc.
    - Voice interface: https://your-app.onrender.com/voice
    
For local development:
    Run: python -m app.main
    - FastAPI: http://localhost:8000
    - Streamlit: http://localhost:8501
    - Root redirects to /app which proxies to Streamlit
"""
import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from app.config import settings
from app.models.schemas import (
    QueryRequest, 
    QueryResponse, 
    IngestionResponse, 
    ChatHistoryItem,
    HealthResponse,
    SourceInfo
)
from app.services.rag import RAGService
from app.services.ingestion import IngestionService
from app.core.tts import TTSService
from app.core.live_api import live_api_service
from app.utils.logging_config import app_logger, error_logger
from fastapi.responses import Response, StreamingResponse, FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
import httpx

# Initialize FastAPI app
app = FastAPI(
    title="DevKraft RAG API",
    description="Simple RAG system with Gemini and Local LLM support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = RAGService()
ingestion_service = IngestionService()
tts_service = TTSService()

# Mount static files for voice interface
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app_logger.info("FastAPI application initialized")


# Startup event to launch Streamlit alongside FastAPI
@app.on_event("startup")
async def startup_event():
    """
    Launch Streamlit in the background when FastAPI starts.
    This allows both services to run from a single Render deployment.
    
    Set START_STREAMLIT=false environment variable to disable auto-start.
    """
    # Check if we should start Streamlit
    should_start = os.getenv("START_STREAMLIT", "true").lower() == "true"
    
    if not should_start:
        app_logger.info("Streamlit auto-start disabled (START_STREAMLIT=false)")
        return
    
    import subprocess
    import sys
    import threading
    
    def start_streamlit():
        """Start Streamlit server in a separate thread."""
        try:
            # Get the port FastAPI is running on
            port = int(os.getenv("PORT", 8000))
            
            # Start Streamlit on port 8501 internally
            # Set API_URL environment variable so Streamlit knows where to find the API
            env = os.environ.copy()
            env["API_URL"] = f"http://localhost:{port}"
            
            subprocess.run(
                [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
                 "--server.port", "8501", "--server.headless", "true",
                 "--server.address", "0.0.0.0"],
                env=env,
                check=False
            )
        except Exception as e:
            app_logger.error(f"Error starting Streamlit: {e}")
    
    # Start Streamlit in a background thread
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    streamlit_thread.start()
    app_logger.info("Started Streamlit on internal port 8501 in background")


@app.get("/")
async def root():
    """Root endpoint - redirects to Streamlit UI."""
    return RedirectResponse(url="/app")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        message="All services are operational"
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a RAG query.
    
    Args:
        request: Query request with user query and model type
        
    Returns:
        Generated response with optional thinking and sources
    """
    try:
        app_logger.info(f"Received query request: model_type={request.model_type}")
        
        response, thinking, chat_id, sources = rag_service.query(
            user_query=request.query,
            model_type=request.model_type,
            chat_id=request.chat_id
        )
        
        return QueryResponse(
            response=response,
            thinking=thinking,
            chat_id=chat_id,
            sources=sources
        )
        
    except Exception as e:
        error_logger.error(f"Query endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query-stream")
async def query_stream(request: QueryRequest):
    """
    Process a RAG query with streaming response.
    
    Args:
        request: Query request with user query and model type
        
    Returns:
        Server-Sent Events stream with response chunks
    """
    try:
        app_logger.info(f"Received streaming query request: model_type={request.model_type}")
        
        return StreamingResponse(
            rag_service.query_stream(
                user_query=request.query,
                model_type=request.model_type,
                chat_id=request.chat_id
            ),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        error_logger.error(f"Streaming query endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload", response_model=IngestionResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and ingest a document.
    
    Args:
        file: Uploaded file
        
    Returns:
        Ingestion result
    """
    try:
        app_logger.info(f"Received file upload: {file.filename}")
        
        # Save uploaded file to generate_embeddings folder
        file_path = Path(settings.generate_embeddings_folder) / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        app_logger.info(f"Saved uploaded file to: {file_path}")
        
        # Ingest the document
        success, message = ingestion_service.ingest_document(str(file_path))
        
        return IngestionResponse(
            success=success,
            message=message,
            filename=file.filename
        )
        
    except Exception as e:
        error_logger.error(f"Upload endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest-all")
async def ingest_all():
    """
    Ingest all documents in the generate_embeddings folder.
    
    Returns:
        List of ingestion results
    """
    try:
        app_logger.info("Starting bulk ingestion")
        
        results = ingestion_service.ingest_all_documents()
        
        return {
            "total": len(results),
            "results": [
                {
                    "filename": filename,
                    "success": success,
                    "message": message
                }
                for filename, success, message in results
            ]
        }
        
    except Exception as e:
        error_logger.error(f"Ingest-all endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest-website", response_model=IngestionResponse)
async def ingest_website(request: dict):
    """
    Ingest content from a website URL.
    
    Args:
        request: Dictionary with 'url' key containing the website URL
        
    Returns:
        Ingestion result
    """
    try:
        url = request.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        app_logger.info(f"Received website ingestion request: {url}")
        
        # Ingest the website
        success, message = ingestion_service.ingest_website(url)
        
        return IngestionResponse(
            success=success,
            message=message,
            filename=url
        )
        
    except Exception as e:
        error_logger.error(f"Ingest website endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats", response_model=List[ChatHistoryItem])
async def get_chats(limit: int = 10):
    """
    Get recent chat sessions.
    
    Args:
        limit: Maximum number of chats to return
        
    Returns:
        List of recent chat metadata
    """
    try:
        app_logger.info(f"Fetching recent chats with limit={limit}")
        
        chats = rag_service.get_recent_chats(limit=limit)
        
        return [ChatHistoryItem(**chat) for chat in chats]
        
    except Exception as e:
        error_logger.error(f"Get chats endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    """
    Get full chat history for a session.
    
    Args:
        chat_id: Chat session ID
        
    Returns:
        Full chat history
    """
    try:
        app_logger.info(f"Fetching chat history for chat_id={chat_id}")
        
        chat_data = rag_service.get_chat_history(chat_id)
        
        return chat_data
        
    except Exception as e:
        error_logger.error(f"Get chat endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts")
async def text_to_speech(request: dict):
    """
    Convert text to speech audio.
    
    Args:
        request: Dictionary with 'text' field
        
    Returns:
        Audio file as WAV
    """
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text field is required")
        
        app_logger.info(f"TTS request for text: {text[:50]}...")
        
        audio_data = tts_service.text_to_speech(text)
        
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=speech.wav"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"TTS endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generate-token")
async def generate_token():
    """
    Generate an ephemeral token for Live API client-side access.
    
    Returns:
        Token information including the token string and expiry times
    """
    try:
        app_logger.info("Generating ephemeral token for Live API")
        token_info = live_api_service.generate_ephemeral_token()
        return token_info
    except Exception as e:
        error_logger.error(f"Token generation endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/function-declarations")
async def get_function_declarations():
    """
    Get function declarations for RAG operations in Live API.
    
    Returns:
        List of function declarations
    """
    try:
        return {
            "functions": live_api_service.get_rag_function_declarations()
        }
    except Exception as e:
        error_logger.error(f"Function declarations endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search-knowledge-base")
async def search_knowledge_base(request: dict):
    """
    Search the knowledge base for relevant information.
    This is called by the Live API as a tool function.
    
    Args:
        request: Dictionary with 'query' and optional 'top_k'
        
    Returns:
        Search results from the vector database
    """
    try:
        query = request.get("query", "")
        top_k = request.get("top_k", 3)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        app_logger.info(f"RAG search request: query='{query[:50]}...', top_k={top_k}")
        
        # Use gemini embedding for search (cloud storage)
        query_embedding = rag_service.gemini_embedding.embed_query(query)
        results = rag_service.storage.search_cloud(
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Format results for the Live API
        formatted_results = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted_results.append({
                "header": metadata.get("header", ""),
                "text": result.get("text", ""),
                "page": metadata.get("page", 0),
                "filename": metadata.get("filename", ""),
                "score": result.get("score", 0.0)
            })
        
        app_logger.info(f"Found {len(formatted_results)} results for query")
        
        return {
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"Search knowledge base endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _reverse_proxy_handler(request: Request, path: str):
    """
    Internal handler to proxy requests to Streamlit.
    Handles both HTTP requests and WebSocket connections.
    """
    client = httpx.AsyncClient(base_url="http://localhost:8501", timeout=30.0)
    url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))
    
    # Prepare headers, excluding host-related headers
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        # Forward the request to Streamlit
        proxy_request = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=await request.body(),
        )
        proxy_response = await client.send(proxy_request, stream=True)
        
        # Prepare response headers
        response_headers = dict(proxy_response.headers)
        response_headers.pop("content-encoding", None)
        response_headers.pop("content-length", None)
        response_headers.pop("transfer-encoding", None)
        
        # Stream the response back
        async def stream_response():
            try:
                async for chunk in proxy_response.aiter_bytes():
                    yield chunk
            finally:
                await proxy_response.aclose()
                await client.aclose()
        
        return StreamingResponse(
            stream_response(),
            status_code=proxy_response.status_code,
            headers=response_headers,
            media_type=proxy_response.headers.get("content-type"),
        )
    except httpx.ConnectError:
        await client.aclose()
        app_logger.error("Cannot connect to Streamlit on port 8501")
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>DevKraft RAG - Loading</title>
                <meta http-equiv="refresh" content="3">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .container {
                        text-align: center;
                    }
                    .spinner {
                        border: 4px solid rgba(255, 255, 255, 0.3);
                        border-radius: 50%;
                        border-top: 4px solid white;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 DevKraft RAG</h1>
                    <div class="spinner"></div>
                    <p>Streamlit is starting up...</p>
                    <p><small>This page will auto-refresh in a moment.</small></p>
                </div>
            </body>
            </html>
            """,
            status_code=503
        )
    except Exception as e:
        await client.aclose()
        app_logger.error(f"Error proxying to Streamlit: {e}")
        raise HTTPException(status_code=502, detail=f"Error connecting to Streamlit: {str(e)}")


@app.api_route("/app/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def streamlit_proxy_with_path(request: Request, path: str):
    """
    Proxy all requests to Streamlit with path.
    This makes Streamlit accessible through the main FastAPI service.
    """
    return await _reverse_proxy_handler(request, f"/{path}")


@app.api_route("/app", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def streamlit_proxy_root(request: Request):
    """
    Proxy root /app requests to Streamlit.
    This makes Streamlit accessible through the main FastAPI service.
    """
    return await _reverse_proxy_handler(request, "/")


@app.get("/voice")
async def voice_interface():
    """
    Serve the voice interface HTML page.
    
    Returns:
        HTML page for voice interaction
    """
    voice_html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "voice.html")
    if os.path.exists(voice_html_path):
        return FileResponse(voice_html_path)
    else:
        raise HTTPException(status_code=404, detail="Voice interface not found")





if __name__ == "__main__":
    import uvicorn
    
    # Use PORT environment variable if available (for cloud platforms like Render)
    # Otherwise default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    
    # Start FastAPI on the configured port
    # The startup event handler will automatically start Streamlit
    app_logger.info(f"Starting FastAPI on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
