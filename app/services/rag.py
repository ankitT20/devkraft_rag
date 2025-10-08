"""
RAG (Retrieval-Augmented Generation) service for query processing.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from uuid import uuid4

from app.config import settings
from app.core.embeddings import GeminiEmbedding, LocalEmbedding
from app.core.llm import GeminiLLM, LocalLLM
from app.core.storage import QdrantStorage
from app.utils.logging_config import app_logger, error_logger


class RAGService:
    """
    Service for RAG-based query processing with chat history management.
    """
    
    def __init__(self):
        """Initialize RAG service with all required components."""
        self.gemini_embedding = GeminiEmbedding()
        self.local_embedding = LocalEmbedding()
        self.gemini_llm = GeminiLLM()
        self.local_llm = LocalLLM()
        self.storage = QdrantStorage()
        
        # Ensure user_chat folder exists
        Path(settings.user_chat_folder).mkdir(parents=True, exist_ok=True)
        
        app_logger.info("Initialized RAGService")
    
    def query(
        self, 
        user_query: str, 
        model_type: str = "gemini",
        chat_id: Optional[str] = None
    ) -> Tuple[str, Optional[str], str, List[Dict]]:
        """
        Process a user query using RAG.
        
        Args:
            user_query: User's question
            model_type: "gemini" or "qwen3"
            chat_id: Optional chat session ID
            
        Returns:
            Tuple of (response, thinking_text, chat_id, sources)
        """
        try:
            app_logger.info(f"Processing RAG query with model_type={model_type}")
            
            # Create or load chat history
            if not chat_id:
                chat_id = str(uuid4())
            
            chat_history = self._load_chat_history(chat_id)
            
            # Generate query embedding and retrieve context
            if model_type == "gemini":
                query_embedding = self.gemini_embedding.embed_query(user_query)
                search_results = self.storage.search_cloud(query_embedding, limit=4)
            else:  # qwen3
                query_embedding = self.local_embedding.embed_query(user_query)
                # search_docker handles fallback from localhost to cloud docker collection
                search_results = self.storage.search_docker(query_embedding, limit=4)
            
            # Build context from search results
            context = self._build_context(search_results)
            
            # Generate response with source tracking
            thinking = None
            used_sources = []
            if model_type == "gemini":
                response, used_sources = self.gemini_llm.generate_response_with_sources(
                    user_query, 
                    context, 
                    chat_history
                )
            else:  # qwen3
                response, thinking, used_sources = self.local_llm.generate_response_with_sources(
                    user_query, 
                    context, 
                    chat_history
                )
            
            # Extract actual sources based on used_sources indices
            sources = self._extract_sources(search_results, used_sources)
            
            # Update chat history
            chat_history.append({
                "role": "user",
                "content": user_query,
                "timestamp": datetime.now().isoformat()
            })
            chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "thinking": thinking,
                "sources": sources
            })
            
            self._save_chat_history(chat_id, chat_history, model_type)
            
            app_logger.info(f"Successfully processed RAG query for chat_id={chat_id}")
            return response, thinking, chat_id, sources
            
        except Exception as e:
            error_logger.error(f"Failed to process RAG query: {e}")
            raise
    
    def _build_context(self, search_results: List[Dict]) -> str:
        """
        Build context string from search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted context string
        """
        if not search_results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"[Document {i}]\n{result['text']}")
        
        return "\n\n".join(context_parts)
    
    def _extract_sources(self, search_results: List[Dict], used_indices: List[int]) -> List[Dict]:
        """
        Extract sources based on document indices used by the LLM.
        
        Args:
            search_results: All search results
            used_indices: List of document indices (1-based) used by the LLM
            
        Returns:
            List of source information dictionaries (max 3)
        """
        sources = []
        
        # If no indices provided, use all sources in order
        if not used_indices:
            used_indices = list(range(1, min(4, len(search_results) + 1)))
        
        # Limit to first 3 sources
        for idx in used_indices[:3]:
            # Convert to 0-based index
            if 1 <= idx <= len(search_results):
                result = search_results[idx - 1]
                metadata = result.get("metadata", {})
                
                source = {
                    "header": metadata.get("header", "Unknown"),
                    "page": metadata.get("page", 1),
                    "filename": metadata.get("filename", "Unknown"),
                    "text": result.get("text", ""),
                    "chunkno": metadata.get("chunkno", 1)
                }
                sources.append(source)
        
        return sources
    
    def _load_chat_history(self, chat_id: str) -> List[Dict]:
        """
        Load chat history from file.
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            List of chat messages
        """
        chat_file = Path(settings.user_chat_folder) / f"{chat_id}.json"
        
        if chat_file.exists():
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("messages", [])
            except Exception as e:
                error_logger.error(f"Failed to load chat history {chat_id}: {e}")
                return []
        
        return []
    
    def _save_chat_history(self, chat_id: str, messages: List[Dict], model_type: str):
        """
        Save chat history to file.
        
        Args:
            chat_id: Chat session ID
            messages: List of chat messages
            model_type: Model type used
        """
        chat_file = Path(settings.user_chat_folder) / f"{chat_id}.json"
        
        try:
            data = {
                "chat_id": chat_id,
                "model_type": model_type,
                "created_at": messages[0]["timestamp"] if messages else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": messages
            }
            
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            app_logger.info(f"Saved chat history for chat_id={chat_id}")
            
        except Exception as e:
            error_logger.error(f"Failed to save chat history {chat_id}: {e}")
    
    def get_recent_chats(self, limit: int = 10) -> List[Dict]:
        """
        Get recent chat sessions.
        
        Args:
            limit: Maximum number of chats to return
            
        Returns:
            List of chat metadata (excludes empty chats)
        """
        chat_folder = Path(settings.user_chat_folder)
        chat_files = sorted(
            chat_folder.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        recent_chats = []
        for chat_file in chat_files[:limit * 2]:  # Get more to filter out empty ones
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
                    
                    # Only include chats with at least 1 message
                    if len(messages) > 0:
                        # Get first user message as preview
                        preview = next(
                            (msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                             for msg in messages if msg["role"] == "user"),
                            "No messages"
                        )
                        
                        recent_chats.append({
                            "chat_id": data.get("chat_id"),
                            "model_type": data.get("model_type", "unknown"),
                            "preview": preview,
                            "updated_at": data.get("updated_at"),
                            "message_count": len(messages)
                        })
                        
                        if len(recent_chats) >= limit:
                            break
            except Exception as e:
                error_logger.error(f"Failed to load chat file {chat_file}: {e}")
        
        return recent_chats
    
    def get_chat_history(self, chat_id: str) -> Dict:
        """
        Get full chat history for a chat session.
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            Chat data dictionary
        """
        chat_file = Path(settings.user_chat_folder) / f"{chat_id}.json"
        
        if chat_file.exists():
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                error_logger.error(f"Failed to load chat history {chat_id}: {e}")
        
        return {"messages": []}
