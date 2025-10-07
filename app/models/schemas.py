"""
Pydantic schemas for request/response validation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    query: str = Field(..., description="User query text", min_length=1)
    model_type: str = Field(default="gemini", description="Model type: 'gemini' or 'qwen3'")
    chat_id: Optional[str] = Field(None, description="Optional chat session ID")


class SourceInfo(BaseModel):
    """Model for source information."""
    index: int = Field(..., description="Source index")
    title: str = Field(..., description="Title or header from the source")
    source: str = Field(..., description="Source filename")
    page: Any = Field(..., description="Page number or N/A")
    chunkno: str = Field(default="N/A", description="Chunk number")
    score: float = Field(..., description="Relevance score")
    text: str = Field(default="", description="Original chunk text")
    point_id: str = Field(default="", description="Qdrant point ID")


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    response: str = Field(..., description="Generated response")
    thinking: Optional[str] = Field(None, description="Thinking process (for qwen3)")
    chat_id: str = Field(..., description="Chat session ID")
    sources: List[SourceInfo] = Field(default_factory=list, description="Sources used in response")


class IngestionResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool = Field(..., description="Whether ingestion was successful")
    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Name of the ingested file")


class ChatHistoryItem(BaseModel):
    """Model for chat history item."""
    chat_id: str = Field(..., description="Chat session ID")
    model_type: str = Field(..., description="Model type used")
    preview: str = Field(..., description="Preview of first message")
    updated_at: str = Field(..., description="Last update timestamp")
    message_count: int = Field(..., description="Number of messages in chat")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
