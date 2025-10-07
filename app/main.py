"""
FastAPI application for RAG system.
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
from app.utils.logging_config import app_logger, error_logger
from fastapi.responses import Response

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

app_logger.info("FastAPI application initialized")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="ok",
        message="DevKraft RAG API is running"
    )


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
