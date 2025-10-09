"""
Configuration module for the RAG application.
Centralized configuration using pydantic-settings with environment variable support.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    qdrant_api_key: str = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))
    hf_token: str = Field(default_factory=lambda: os.getenv("HF_TOKEN", ""))
    
    # MongoDB Configuration
    mongo_uri: str = Field(default_factory=lambda: os.getenv("MONGO_URI", ""))
    mongo_db_name: str = "devkraft_rag"
    mongo_collection_name: str = "chat_history"
    
    # Qdrant Configuration
    qdrant_cloud_url: str = "https://7f6a07f7-8039-4473-acbf-be311a53b2bc.europe-west3-0.gcp.cloud.qdrant.io:6333"
    qdrant_docker_url: str = "http://localhost:6333"
    qdrant_cloud_collection: str = "bootcamp_rag_cloud"
    qdrant_docker_collection: str = "bootcamp_rag_docker"
    
    # LM Studio Configuration
    lmstudio_url: str = "http://127.0.0.1:1234"
    
    # Model Configuration
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_live_model: str = "models/gemini-2.5-flash-native-audio-preview-09-2025"
    local_embedding_model: str = "text-embedding-embeddinggemma-300m-qat"
    local_chat_model: str = "qwen/qwen3-1.7b"
    hf_embedding_model: str = "google/embeddinggemma-300m"
    hf_chat_model: str = "Qwen/Qwen3-1.7B"
    
    # Vector dimensions
    gemini_embedding_dim: int = 3072
    local_embedding_dim: int = 768
    
    # Chunking configuration
    chunk_size: int = 2000  # characters
    chunk_overlap: int = 400  # characters
    
    # Paths
    generate_embeddings_folder: str = "generate_embeddings"
    stored_folder: str = "generate_embeddings/stored"
    stored_docker_only_folder: str = "generate_embeddings/stored_in_q_docker_only"
    stored_cloud_only_folder: str = "generate_embeddings/stored_in_q_cloud_only"
    user_chat_folder: str = "user_chat"
    logs_folder: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
