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
    SourceInfo,
    LiveSessionRequest,
    LiveSessionResponse,
    LiveTextRequest
)
from app.services.rag import RAGService
from app.services.ingestion import IngestionService
from app.core.tts import TTSService
from app.core.live_api import LiveAPIService
from app.utils.logging_config import app_logger, error_logger
from fastapi.responses import Response, StreamingResponse

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
live_api_service = LiveAPIService()

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


@app.post("/live/start-session", response_model=LiveSessionResponse)
async def start_live_session(request: LiveSessionRequest):
    """
    Start a Live API session.
    
    Args:
        request: Live API session request with language
        
    Returns:
        Session ID and status
    """
    try:
        app_logger.info(f"Starting Live API session for language: {request.language}")
        
        # Create a new session ID
        session_id = live_api_service.create_session_id()
        
        # Store session metadata
        live_api_service.store_session(session_id, {
            "language": request.language,
            "created_at": None,  # Will be set when actual session is created
            "status": "initialized"
        })
        
        return LiveSessionResponse(
            session_id=session_id,
            status="ready",
            language=request.language,
            message=f"Live API session initialized for {request.language}"
        )
        
    except Exception as e:
        error_logger.error(f"Failed to start Live API session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/live/send-audio")
async def send_audio_to_live(audio: UploadFile = File(...), language: str = "en-IN"):
    """
    Send audio to Live API session and get response.
    
    Args:
        audio: Audio file from microphone
        language: Language code
        
    Returns:
        Audio response in WAV format
    """
    try:
        app_logger.info(f"Receiving audio input for Live API (language: {language})")
        
        # Read audio file
        audio_data = await audio.read()
        
        # Create a Live API session
        async with live_api_service.client.aio.live.connect(
            model=live_api_service.model,
            config=live_api_service.get_config(language)
        ) as session:
            # Send audio data to Live API
            await session.send(input={"data": audio_data, "mime_type": "audio/wav"})
            
            # Collect response
            response_text = ""
            audio_response = b""
            transcription = ""
            
            turn = session.receive()
            async for response in turn:
                if response.data:
                    audio_response += response.data
                if response.text:
                    response_text += response.text
                    if not transcription:
                        transcription = "Voice input received"
            
            app_logger.info(f"Received audio response: {len(audio_response)} bytes, text: {response_text[:100]}...")
            
            if audio_response:
                # Convert raw PCM audio to WAV format
                import struct
                sample_rate = 24000
                num_channels = 1
                bits_per_sample = 16
                data_size = len(audio_response)
                bytes_per_sample = bits_per_sample // 8
                block_align = num_channels * bytes_per_sample
                byte_rate = sample_rate * block_align
                chunk_size = 36 + data_size
                
                wav_header = struct.pack(
                    "<4sI4s4sIHHIIHH4sI",
                    b"RIFF",
                    chunk_size,
                    b"WAVE",
                    b"fmt ",
                    16,
                    1,
                    num_channels,
                    sample_rate,
                    byte_rate,
                    block_align,
                    bits_per_sample,
                    b"data",
                    data_size
                )
                
                wav_data = wav_header + audio_response
                
                return Response(
                    content=wav_data,
                    media_type="audio/wav",
                    headers={
                        "X-Response-Text": response_text,
                        "X-Transcription": transcription,
                        "Content-Disposition": "attachment; filename=response.wav"
                    }
                )
            else:
                raise HTTPException(status_code=500, detail="No audio response received")
        
    except Exception as e:
        error_logger.error(f"Failed to process audio input: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/live/send-text")
async def send_text_to_live(request: LiveTextRequest):
    """
    Send text to Live API session and get response with audio.
    
    Args:
        request: Live API text request
        
    Returns:
        Audio data in WAV format and text response
    """
    try:
        app_logger.info(f"Sending text to Live API: {request.text[:50]}... (language: {request.language})")
        
        # Create a temporary session for this request
        async with live_api_service.client.aio.live.connect(
            model=live_api_service.model,
            config=live_api_service.get_config(request.language)
        ) as session:
            # Send text
            await live_api_service.send_text(session, request.text)
            
            # Collect response
            response_text = ""
            audio_data = b""
            
            turn = session.receive()
            async for response in turn:
                if response.data:
                    audio_data += response.data
                if response.text:
                    response_text += response.text
            
            app_logger.info(f"Received response: {response_text[:100]}... with {len(audio_data)} bytes of audio")
            
            if audio_data:
                # Convert raw PCM audio to WAV format
                import struct
                sample_rate = 24000
                num_channels = 1
                bits_per_sample = 16
                data_size = len(audio_data)
                bytes_per_sample = bits_per_sample // 8
                block_align = num_channels * bytes_per_sample
                byte_rate = sample_rate * block_align
                chunk_size = 36 + data_size
                
                wav_header = struct.pack(
                    "<4sI4s4sIHHIIHH4sI",
                    b"RIFF",
                    chunk_size,
                    b"WAVE",
                    b"fmt ",
                    16,
                    1,
                    num_channels,
                    sample_rate,
                    byte_rate,
                    block_align,
                    bits_per_sample,
                    b"data",
                    data_size
                )
                
                wav_data = wav_header + audio_data
                
                return Response(
                    content=wav_data,
                    media_type="audio/wav",
                    headers={
                        "X-Response-Text": response_text,
                        "Content-Disposition": "attachment; filename=response.wav"
                    }
                )
            else:
                return {
                    "status": "success",
                    "text": response_text,
                    "has_audio": False,
                    "message": "Text sent and response received (no audio)"
                }
        
    except Exception as e:
        error_logger.error(f"Failed to send text to Live API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
