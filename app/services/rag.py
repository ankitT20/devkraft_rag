"""
RAG (Retrieval-Augmented Generation) service for query processing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from app.config import settings
from app.core.chat_storage import ChatStorageService
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
        self.chat_storage = ChatStorageService()

        # Ensure user_chat folder exists (for fallback)
        Path(settings.user_chat_folder).mkdir(parents=True, exist_ok=True)

        app_logger.info("Initialized RAGService")

    def query(
        self, user_query: str, model_type: str = "gemini", chat_id: Optional[str] = None
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
                    user_query, context, chat_history
                )
            else:  # qwen3
                response, thinking, used_sources = self.local_llm.generate_response_with_sources(
                    user_query, context, chat_history
                )

            # Extract actual sources based on used_sources indices
            sources = self._extract_sources(search_results, used_sources)

            # Update chat history
            chat_history.append(
                {"role": "user", "content": user_query, "timestamp": datetime.now().isoformat()}
            )
            chat_history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "thinking": thinking,
                    "sources": sources,
                }
            )

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
                    "chunkno": metadata.get("chunkno", 1),
                }
                sources.append(source)

        return sources

    def _load_chat_history(self, chat_id: str) -> List[Dict]:
        """
        Load chat history from MongoDB or JSON file fallback.

        Args:
            chat_id: Chat session ID

        Returns:
            List of chat messages
        """
        return self.chat_storage.load_chat_history(chat_id)

    def _save_chat_history(self, chat_id: str, messages: List[Dict], model_type: str):
        """
        Save chat history to MongoDB or JSON file fallback.

        Args:
            chat_id: Chat session ID
            messages: List of chat messages
            model_type: Model type used
        """
        self.chat_storage.save_chat_history(chat_id, messages, model_type)

    def get_recent_chats(self, limit: int = 10) -> List[Dict]:
        """
        Get recent chat sessions from MongoDB or JSON file fallback.

        Args:
            limit: Maximum number of chats to return

        Returns:
            List of chat metadata (excludes empty chats)
        """
        return self.chat_storage.get_recent_chats(limit)

    def get_chat_history(self, chat_id: str) -> Dict:
        """
        Get full chat history for a chat session from MongoDB or JSON file fallback.

        Args:
            chat_id: Chat session ID

        Returns:
            Chat data dictionary
        """
        return self.chat_storage.get_chat_history(chat_id)

    def query_stream(
        self, user_query: str, model_type: str = "gemini", chat_id: Optional[str] = None
    ):
        """
        Process a user query using RAG with streaming response.

        Args:
            user_query: User's question
            model_type: "gemini" or "qwen3" (currently only gemini supports streaming)
            chat_id: Optional chat session ID

        Yields:
            Streaming response chunks and metadata
        """
        try:
            app_logger.info(f"Processing streaming RAG query with model_type={model_type}")

            # Create or load chat history
            if not chat_id:
                chat_id = str(uuid4())

            chat_history = self._load_chat_history(chat_id)

            # Generate query embedding and retrieve context
            if model_type == "gemini":
                query_embedding = self.gemini_embedding.embed_query(user_query)
                search_results = self.storage.search_cloud(query_embedding, limit=4)
            else:  # qwen3
                # For now, qwen3 doesn't support streaming, so we could fall back
                # or return an error. Let's yield an error message.
                yield 'data: {"error": "Streaming is currently only supported for Gemini model"}\n\n'
                return

            # Build context from search results
            context = self._build_context(search_results)

            # Yield initial metadata
            yield f'data: {{"type": "start", "chat_id": "{chat_id}"}}\n\n'

            # Generate streaming response
            full_response = ""
            sources = []

            for chunk in self.gemini_llm.generate_response_with_sources_stream(
                user_query, context, chat_history
            ):
                # Check if this is the sources marker
                if chunk.startswith("\n__SOURCES__:"):
                    sources_str = chunk.replace("\n__SOURCES__:", "")
                    if sources_str and sources_str != "":
                        source_indices = [int(x) for x in sources_str.split(",") if x]
                        sources = self._extract_sources(search_results, source_indices)
                else:
                    full_response += chunk
                    # Yield the text chunk
                    import json as json_lib

                    yield f"data: {json_lib.dumps({'type': 'chunk', 'text': chunk})}\n\n"

            # Clean the full response (remove SOURCES line)
            full_response = self._remove_sources_line_from_text(full_response)

            # Update chat history
            chat_history.append(
                {"role": "user", "content": user_query, "timestamp": datetime.now().isoformat()}
            )
            chat_history.append(
                {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                    "thinking": None,
                    "sources": sources,
                }
            )

            self._save_chat_history(chat_id, chat_history, model_type)

            # Yield final metadata with sources
            import json as json_lib

            yield f"data: {json_lib.dumps({'type': 'end', 'sources': sources, 'chat_id': chat_id})}\n\n"

            app_logger.info(f"Successfully processed streaming RAG query for chat_id={chat_id}")

        except Exception as e:
            error_logger.error(f"Failed to process streaming RAG query: {e}")
            import json as json_lib

            yield f"data: {json_lib.dumps({'type': 'error', 'error': str(e)})}\n\n"

    def _remove_sources_line_from_text(self, response: str) -> str:
        """Remove the SOURCES line from the response."""
        import re

        # Remove the entire SOURCES line
        cleaned = re.sub(r"\n*SOURCES:\s*[0-9,\s]+\s*$", "", response, flags=re.IGNORECASE)
        return cleaned.strip()
