"""
LLM services for chat completions using Gemini and Local/HF models.
"""
import os
import re
import requests
from typing import List, Dict, Optional, Tuple, Iterator, AsyncIterator
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
        Generate response using Gemini (legacy method, kept for compatibility).
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Returns:
            Generated response text
        """
        response, _ = self.generate_response_with_sources(query, context, chat_history)
        return response
    
    def generate_response_with_sources(self, query: str, context: str, chat_history: List[Dict[str, str]] = None) -> Tuple[str, List[int]]:
        """
        Generate response using Gemini with source tracking.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Returns:
            Tuple of (response_text, list of document indices used)
        """
        try:
            app_logger.info("Generating Gemini response with source tracking")
            
            # Build the prompt
            prompt = self._build_prompt_with_sources(query, context)
            
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
            
            # Extract sources from response
            sources = self._extract_source_indices(result)
            
            # Remove the SOURCES line from the result
            result = self._remove_sources_line(result)
            
            app_logger.info(f"Successfully generated Gemini response with sources: {sources}")
            return result, sources
            
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
    
    def _build_prompt_with_sources(self, query: str, context: str) -> str:
        """Build the RAG prompt with source tracking."""
        prompt = f"""You are a helpful and informative bot that answers questions using text from the reference passages included below. 
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.

However, you are talking to a non-technical audience, so be sure to break down complicated concepts and strike a friendly and conversational tone. 
If the passage is irrelevant to the answer, you may ignore it.

CONTEXT: {context}

QUESTION: {query}

ANSWER: (First provide your answer, then on a new line add "SOURCES: " followed by ONLY the document numbers you actually used in your answer, comma-separated, in order of relevance. If you did not use any documents or they were not relevant, write "SOURCES: 0")"""
        return prompt
    
    def _extract_source_indices(self, response: str) -> List[int]:
        """Extract source document indices from response."""
        import re
        sources = []
        
        # Look for "SOURCES: 1, 2, 3" pattern
        match = re.search(r'SOURCES:\s*([0-9,\s]+)', response, re.IGNORECASE)
        if match:
            source_str = match.group(1)
            # Extract all numbers (ignore 0 which means no sources used)
            numbers = re.findall(r'\d+', source_str)
            sources = [int(n) for n in numbers if 1 <= int(n) <= 4]
        
        return sources
    
    def _remove_sources_line(self, response: str) -> str:
        """Remove the SOURCES line from the response."""
        # Remove the entire SOURCES line
        cleaned = re.sub(r'\n*SOURCES:\s*[0-9,\s]+\s*$', '', response, flags=re.IGNORECASE)
        return cleaned.strip()
    
    async def generate_response_stream(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming response using Gemini with source tracking.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Yields:
            Response text chunks
        """
        try:
            app_logger.info("Generating Gemini streaming response with source tracking")
            
            # Build the prompt
            prompt = self._build_prompt_with_sources(query, context)
            
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
            
            # Generate streaming response
            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=contents
            )
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text
            
            app_logger.info("Successfully generated Gemini streaming response")
            
        except Exception as e:
            error_logger.error(f"Failed to generate Gemini streaming response: {e}")
            raise


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
        Generate response using Local LLM (legacy method, kept for compatibility).
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Returns:
            Tuple of (response_text, thinking_text)
        """
        response, thinking, _ = self.generate_response_with_sources(query, context, chat_history)
        return response, thinking
    
    def generate_response_with_sources(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str], List[int]]:
        """
        Generate response using Local LLM with source tracking.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Returns:
            Tuple of (response_text, thinking_text, list of document indices used)
        """
        try:
            app_logger.info("Generating local LLM response with source tracking")
            
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
    ) -> Tuple[str, Optional[str], List[int]]:
        """Generate response using LM Studio."""
        prompt = self._build_prompt_with_sources(query, context)
        
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
            timeout=200
        )
        response.raise_for_status()
        
        result = response.json()["choices"][0]["message"]["content"]
        cleaned_response, thinking = self._extract_thinking(result)
        sources = self._extract_source_indices(cleaned_response)
        cleaned_response = self._remove_sources_line(cleaned_response)
        
        app_logger.info("Successfully generated LM Studio response")
        return cleaned_response, thinking, sources
    
    def _generate_with_hf(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, Optional[str], List[int]]:
        """Generate response using HuggingFace."""
        prompt = self._build_prompt_with_sources(query, context)
        
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
        cleaned_response, thinking = self._extract_thinking(result)
        sources = self._extract_source_indices(cleaned_response)
        cleaned_response = self._remove_sources_line(cleaned_response)
        
        app_logger.info("Successfully generated HuggingFace response")
        return cleaned_response, thinking, sources
    
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
    
    def _build_prompt_with_sources(self, query: str, context: str) -> str:
        """Build the RAG prompt with source tracking."""
        prompt = f"""You are a helpful and informative bot that answers questions using text from the reference passages included below. 
Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.

However, you are talking to a non-technical audience, so be sure to break down complicated concepts and strike a friendly and conversational tone. 
If the passage is irrelevant to the answer, you may ignore it.

CONTEXT: {context}

QUESTION: {query}

ANSWER: (First provide your answer, then on a new line add "SOURCES: " followed by ONLY the document numbers you actually used in your answer, comma-separated, in order of relevance. If you did not use any documents or they were not relevant, write "SOURCES: 0")"""
        return prompt
    
    def _extract_source_indices(self, response: str) -> List[int]:
        """Extract source document indices from response."""
        import re
        sources = []
        
        # Look for "SOURCES: 1, 2, 3" pattern
        match = re.search(r'SOURCES:\s*([0-9,\s]+)', response, re.IGNORECASE)
        if match:
            source_str = match.group(1)
            # Extract all numbers (ignore 0 which means no sources used)
            numbers = re.findall(r'\d+', source_str)
            sources = [int(n) for n in numbers if 1 <= int(n) <= 4]
        
        return sources
    
    def _remove_sources_line(self, response: str) -> str:
        """Remove the SOURCES line from the response."""
        import re
        # Remove the entire SOURCES line
        cleaned = re.sub(r'\n*SOURCES:\s*[0-9,\s]+\s*$', '', response, flags=re.IGNORECASE)
        return cleaned.strip()
    
    def _extract_thinking(self, response: str) -> Tuple[str, Optional[str]]:
        """
        Extract thinking block from response if present and remove it from the response.
        
        Args:
            response: Full response text
            
        Returns:
            Tuple of (cleaned_response, thinking_text)
        """
        if "<think>" in response and "</think>" in response:
            start = response.find("<think>")
            end = response.find("</think>") + len("</think>")
            thinking = response[start + len("<think>"):end - len("</think>")].strip()
            cleaned_response = response[:start] + response[end:]
            return cleaned_response.strip(), thinking
        return response, None
    
    async def generate_response_stream(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming response using Local LLM with source tracking.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            chat_history: Optional chat history
            
        Yields:
            Response text chunks
        """
        try:
            app_logger.info("Generating local LLM streaming response with source tracking")
            
            if self.use_fallback:
                async for chunk in self._generate_stream_with_hf(query, context, chat_history):
                    yield chunk
            else:
                try:
                    async for chunk in self._generate_stream_with_lmstudio(query, context, chat_history):
                        yield chunk
                except Exception as e:
                    app_logger.warning(f"LM Studio failed: {e}, falling back to HuggingFace")
                    self.use_fallback = True
                    self.hf_client = InferenceClient(
                        provider="featherless-ai",
                        api_key=settings.hf_token
                    )
                    async for chunk in self._generate_stream_with_hf(query, context, chat_history):
                        yield chunk
                    
        except Exception as e:
            error_logger.error(f"Failed to generate local streaming response: {e}")
            raise
    
    async def _generate_stream_with_lmstudio(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response using LM Studio."""
        prompt = self._build_prompt_with_sources(query, context)
        
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
                "stream": True
            },
            timeout=200,
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]
                    if data == '[DONE]':
                        break
                    try:
                        import json
                        chunk_data = json.loads(data)
                        content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
        
        app_logger.info("Successfully generated LM Studio streaming response")
    
    async def _generate_stream_with_hf(
        self, 
        query: str, 
        context: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response using HuggingFace."""
        prompt = self._build_prompt_with_sources(query, context)
        
        messages = []
        if chat_history:
            messages.extend(chat_history[-5:])  # Last 5 messages
        messages.append({"role": "user", "content": prompt})
        
        stream = self.hf_client.chat.completions.create(
            model=self.hf_model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
        
        app_logger.info("Successfully generated HuggingFace streaming response")
