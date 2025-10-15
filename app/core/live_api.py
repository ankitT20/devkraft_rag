"""
Live API service for generating ephemeral tokens and managing RAG function calls.
"""
import datetime
from typing import List, Dict, Any
from google import genai
from google.genai import types

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class LiveAPIService:
    """
    Service for Live API ephemeral token generation and RAG integration.
    """
    
    def __init__(self):
        """Initialize Live API service with API key rotation support."""
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={'api_version': 'v1alpha'}
        )
        self.model = settings.gemini_live_model
        self.token_call_count = 0  # Track token generation calls for API key rotation
        
        # Initialize second client if second API key is available
        self.client2 = None
        self.has_second_key = False
        if settings.gemini_api_key2:
            try:
                self.client2 = genai.Client(
                    api_key=settings.gemini_api_key2,
                    http_options={'api_version': 'v1alpha'}
                )
                self.has_second_key = True
                app_logger.info(f"Initialized LiveAPIService with model: {self.model} (with API key rotation)")
            except Exception as e:
                error_logger.warning(f"Failed to initialize second Live API client: {e}")
                app_logger.info(f"Initialized LiveAPIService with model: {self.model} (single API key)")
        else:
            app_logger.info(f"Initialized LiveAPIService with model: {self.model} (single API key)")
    
    def generate_ephemeral_token(self) -> Dict[str, Any]:
        """
        Generate an ephemeral token for client-side Live API access.
        
        Returns:
            Dictionary containing token information
        """
        try:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            
            # Increment call counter for API key rotation
            self.token_call_count += 1
            
            # Alternate between API keys for token generation
            if self.has_second_key and self.token_call_count % 2 == 0:
                current_client = self.client2
                app_logger.info(f"Generating ephemeral token (call #{self.token_call_count}, using API key 2)")
            else:
                current_client = self.client
                app_logger.info(f"Generating ephemeral token (call #{self.token_call_count}, using API key 1)")
            
            # Create token with 30 min expiry and 1 min to start new session
            token = current_client.auth_tokens.create(
                config={
                    'uses': 1,  # Single use token for security
                    'expire_time': now + datetime.timedelta(minutes=30),
                    'new_session_expire_time': now + datetime.timedelta(minutes=1),
                }
            )
            
            app_logger.info("Successfully generated ephemeral token for Live API")
            
            return {
                "token": token.name,
                "expires_in": 1800,  # 30 minutes in seconds
                "new_session_expires_in": 60  # 1 minute in seconds
            }
            
        except Exception as e:
            error_logger.error(f"Failed to generate ephemeral token: {e}")
            raise
    
    @staticmethod
    def get_rag_function_declarations() -> List[Dict[str, Any]]:
        """
        Get function declarations for RAG operations.
        
        Returns:
            List of function declarations for Live API
        """
        return [
            {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base (vector database) for relevant information to answer user questions. Use this function when you need to retrieve specific information from uploaded documents.",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant information in the knowledge base"
                        },
                        "top_k": {
                            "type": "number",
                            "description": "Number of top results to return (default: 3)",
                            "default": 3
                        }
                    }
                }
            }
        ]


# Global instance
live_api_service = LiveAPIService()
