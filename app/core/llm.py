"""
LLM services for chat completions using Gemini and Local/HF models.
"""
import os
import requests
from typing import List, Dict, Optional, Tuple
from google import genai
from google.genai import types
from huggingface_hub import InferenceClient

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class GeminiLLM:
    """
    Gemini LLM service using gemini-2.5-flash.
    """
    
    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_chat_model
        app_logger.info(f"Initialized GeminiLLM with model: {self.model}")
    
    def generate_response(self, query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Generate response using Gemini.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Returns:
            Generated response text
        """
        try:
            app_logger.info("Generating Gemini response")
            
            # Build the prompt
            prompt = self._build_prompt(query, context)
            
            # Build contents with history
            contents = []
            if chat_history:
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    ))
            
            # Add current query
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            ))
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            
            result = response.text
            app_logger.info("Successfully generated Gemini response")
            return result
            
        except Exception as e:
            error_logger.error(f"Failed to generate Gemini response: {e}")
            raise
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the RAG prompt."""
        prompt = f"""You are a helpful and informative bot that answers questions using text from the reference passage included below. 
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.

However, you are talking to a non-technical audience, so be sure to break down complicated concepts and strike a friendly and conversational tone. 
If the passage is irrelevant to the answer, you may ignore it.

CONTEXT: {context}

QUESTION: {query}

ANSWER:"""
        return prompt


class LocalLLM:
    """
    Local LLM service using LM Studio with HuggingFace fallback.
    Supports thinking blocks for qwen models.
    """
    
    def __init__(self):
        """Initialize local LLM client with HuggingFace fallback."""
        self.lmstudio_url = settings.lmstudio_url
        self.local_model = settings.local_chat_model
        self.hf_model = settings.hf_chat_model
        self.use_fallback = False
        
        # Test LM Studio availability
        if not self._test_lmstudio():
            app_logger.warning("LM Studio not available, using HuggingFace fallback")
            self.use_fallback = True
            self.hf_client = InferenceClient(
                provider="featherless-ai",
                api_key=settings.hf_token
            )
        else:
            app_logger.info(f"Initialized LocalLLM with LM Studio: {self.lmstudio_url}")
    
    def _test_lmstudio(self) -> bool:
        """Test if LM Studio is available."""
        try:
            response = requests.get(f"{self.lmstudio_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Generate response using Local LLM.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Returns:
            Tuple of (response_text, thinking_text)
        """
        try:
            app_logger.info("Generating local LLM response")
            
            if self.use_fallback:
                return self._generate_with_hf(query, context, chat_history)
            else:
                try:
                    return self._generate_with_lmstudio(query, context, chat_history)
                except Exception as e:
                    app_logger.warning(f"LM Studio failed: {e}, falling back to HuggingFace")
                    self.use_fallback = True
                    self.hf_client = InferenceClient(
                        provider="featherless-ai",
                        api_key=settings.hf_token
                    )
                    return self._generate_with_hf(query, context, chat_history)
                    
        except Exception as e:
            error_logger.error(f"Failed to generate local response: {e}")
            raise
    
    def _generate_with_lmstudio(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str]]:
        """Generate response using LM Studio."""
        prompt = self._build_prompt(query, context)
        
        messages = []
        if chat_history:
            messages.extend(chat_history[-5:])  # Last 5 messages
        messages.append({"role": "user", "content": prompt})
        
        response = requests.post(
            f"{self.lmstudio_url}/v1/chat/completions",
            json={
                "model": self.local_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()["choices"][0]["message"]["content"]
        thinking = self._extract_thinking(result)
        
        app_logger.info("Successfully generated LM Studio response")
        return result, thinking
    
    def _generate_with_hf(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str]]:
        """Generate response using HuggingFace."""
        prompt = self._build_prompt(query, context)
        
        messages = []
        if chat_history:
            messages.extend(chat_history[-5:])  # Last 5 messages
        messages.append({"role": "user", "content": prompt})
        
        completion = self.hf_client.chat.completions.create(
            model=self.hf_model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        result = completion.choices[0].message.content
        thinking = self._extract_thinking(result)
        
        app_logger.info("Successfully generated HuggingFace response")
        return result, thinking
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the RAG prompt."""
        prompt = f"""You are a helpful and informative bot that answers questions using text from the reference passage included below. 
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.

However, you are talking to a non-technical audience, so be sure to break down complicated concepts and strike a friendly and conversational tone. 
If the passage is irrelevant to the answer, you may ignore it.

CONTEXT: {context}

QUESTION: {query}

ANSWER:"""
        return prompt
    
    def _extract_thinking(self, response: str) -> Optional[str]:
        """
        Extract thinking block from response if present.
        
        Args:
            response: Full response text
            
        Returns:
            Thinking text if found, None otherwise
        """
        if "<think>" in response and "</think>" in response:
            start = response.find("<think>") + len("<think>")
            end = response.find("</think>")
            return response[start:end].strip()
        return None
