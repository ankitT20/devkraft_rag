"""
Gemini Live API service for real-time voice interaction.
Based on the official Gemini Live API quickstart.
"""
import asyncio
import os
from typing import Optional, AsyncGenerator, Dict
import uuid
from google import genai
from google.genai import types

from app.config import settings
from app.utils.logging_config import app_logger, error_logger

# Audio configuration constants
FORMAT_INT16 = "int16"
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024


# Global session storage (in production, use Redis or similar)
_active_sessions: Dict[str, dict] = {}


class LiveAPIService:
    """
    Gemini Live API service for real-time voice interaction.
    """
    
    def __init__(self):
        """Initialize Live API service."""
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=settings.gemini_api_key
        )
        self.model = settings.gemini_live_model
        app_logger.info(f"Initialized LiveAPIService with model: {self.model}")
    
    def get_config(self, language: str = "en-IN") -> types.LiveConnectConfig:
        """
        Get Live API configuration.
        
        Args:
            language: Language code (e.g., 'en-IN', 'hi-IN')
            
        Returns:
            LiveConnectConfig with audio settings
        """
        # Note: According to the docs, native audio output models automatically 
        # choose the appropriate language and don't support explicitly setting 
        # the language code. So we'll add it to the system instruction instead.
        
        system_instruction = f"""You are a helpful AI assistant. 
Please respond in {self._get_language_name(language)} language.
Be conversational and natural in your responses."""
        
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Achird"
                    )
                )
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
            system_instruction=system_instruction
        )
        
        app_logger.info(f"Created Live API config for language: {language}")
        return config
    
    def _get_language_name(self, language_code: str) -> str:
        """
        Get full language name from code.
        
        Args:
            language_code: Language code (e.g., 'en-IN', 'hi-IN')
            
        Returns:
            Language name
        """
        language_map = {
            "en-IN": "English (India)",
            "hi-IN": "Hindi (India)"
        }
        return language_map.get(language_code, "English (India)")
    
    async def create_session(self, language: str = "en-IN"):
        """
        Create a Live API session.
        
        Args:
            language: Language code for the session
            
        Returns:
            Live session object
        """
        try:
            config = self.get_config(language)
            session = await self.client.aio.live.connect(
                model=self.model,
                config=config
            )
            app_logger.info(f"Created Live API session for language: {language}")
            return session
        except Exception as e:
            error_logger.error(f"Failed to create Live API session: {e}")
            raise
    
    async def send_audio(self, session, audio_data: bytes):
        """
        Send audio data to the Live API session.
        
        Args:
            session: Live API session
            audio_data: Raw audio bytes (PCM format)
        """
        try:
            await session.send(
                input={"data": audio_data, "mime_type": "audio/pcm"}
            )
        except Exception as e:
            error_logger.error(f"Failed to send audio: {e}")
            raise
    
    async def send_text(self, session, text: str):
        """
        Send text input to the Live API session.
        
        Args:
            session: Live API session
            text: Text to send
        """
        try:
            await session.send(input=text, end_of_turn=True)
            app_logger.info(f"Sent text to Live API: {text[:50]}...")
        except Exception as e:
            error_logger.error(f"Failed to send text: {e}")
            raise
    
    async def receive_audio(self, session) -> AsyncGenerator[bytes, None]:
        """
        Receive audio responses from the Live API session.
        
        Args:
            session: Live API session
            
        Yields:
            Audio data chunks
        """
        try:
            turn = session.receive()
            async for response in turn:
                if data := response.data:
                    yield data
                if text := response.text:
                    app_logger.info(f"Received text from Live API: {text[:50]}...")
        except Exception as e:
            error_logger.error(f"Failed to receive audio: {e}")
            raise
    
    def create_session_id(self) -> str:
        """
        Create a unique session ID.
        
        Returns:
            Unique session ID
        """
        return str(uuid.uuid4())
    
    def store_session(self, session_id: str, session_data: dict):
        """
        Store session data.
        
        Args:
            session_id: Session ID
            session_data: Session data to store
        """
        _active_sessions[session_id] = session_data
        app_logger.info(f"Stored session: {session_id}")
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        return _active_sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        """
        Remove session data.
        
        Args:
            session_id: Session ID
        """
        if session_id in _active_sessions:
            del _active_sessions[session_id]
            app_logger.info(f"Removed session: {session_id}")
