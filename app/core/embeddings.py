"""
Embedding services for generating embeddings using Gemini and Local/HF models.
"""
import os
import time
import numpy as np
from typing import List, Optional
from google import genai
from google.genai import types
from huggingface_hub import InferenceClient
import requests

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class GeminiEmbedding:
    """
    Gemini embedding service using gemini-embedding-001.
    Output: 3072 dimensions, already normalized by API.
    """
    
    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_embedding_model
        self.api_call_count = 0  # Track API calls for rate limiting
        app_logger.info(f"Initialized GeminiEmbedding with model: {self.model}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents using RETRIEVAL_DOCUMENT task type.
        Implements batching (max 90 per batch) and rate limiting to comply with API limits.
        - Batch limit: 90 requests per batch (API max is 100, using 90 for safety)
        - Rate limit: 90 requests per minute (API max is 100, using 90 for safety)
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (3072 dimensions each)
        """
        try:
            app_logger.info(f"Generating Gemini embeddings for {len(texts)} chunks")
            
            # Check for empty input
            if not texts or len(texts) == 0:
                error_logger.error("Cannot generate embeddings: texts list is empty")
                raise ValueError("texts list cannot be empty")
            
            # Batch processing: max 90 requests per batch
            BATCH_SIZE = 90
            all_embeddings = []
            
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i:i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
                
                app_logger.info(f"Processing batch {batch_num}/{total_batches} with {len(batch)} texts")
                
                # Apply rate limiting: 90 requests per minute
                # After processing a batch, wait if needed to stay under rate limit
                self.api_call_count += len(batch)
                
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                )
                batch_embeddings = [emb.values for emb in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                
                # Rate limiting: wait ~0.7 seconds per request to stay under 90/min
                # For a batch of 90, wait ~63 seconds before next batch
                if i + BATCH_SIZE < len(texts):  # Not the last batch
                    wait_time = len(batch) * 0.7  # ~0.7 sec per request = ~90 req/min
                    app_logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds before next batch")
                    time.sleep(wait_time)
            
            app_logger.info(f"Successfully generated {len(all_embeddings)} Gemini embeddings")
            return all_embeddings
        except Exception as e:
            error_logger.error(f"Failed to generate Gemini embeddings: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query using RETRIEVAL_QUERY task type.
        Implements rate limiting: 10 second delay after every 50 API calls.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector (3072 dimensions)
        """
        try:
            app_logger.info(f"Generating Gemini query embedding")
            
            # Check if we need to apply rate limiting
            self.api_call_count += 1
            if self.api_call_count % 50 == 0:
                app_logger.info(f"Rate limiting: Applied 10 second delay after {self.api_call_count} API calls")
                time.sleep(10)
            
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY"
                )
            )
            embedding = result.embeddings[0].values
            app_logger.info("Successfully generated Gemini query embedding")
            return embedding
        except Exception as e:
            error_logger.error(f"Failed to generate Gemini query embedding: {e}")
            raise


class LocalEmbedding:
    """
    Local embedding service using LM Studio with HuggingFace fallback.
    Output: 768 dimensions, requires normalization.
    """
    
    def __init__(self):
        """Initialize local embedding client with HuggingFace fallback."""
        self.lmstudio_url = settings.lmstudio_url
        self.local_model = settings.local_embedding_model
        self.hf_model = settings.hf_embedding_model
        self.use_fallback = False
        
        # Test LM Studio availability
        if not self._test_lmstudio():
            app_logger.warning("LM Studio not available, using HuggingFace fallback")
            self.use_fallback = True
            self.hf_client = InferenceClient(api_key=settings.hf_token)
        else:
            app_logger.info(f"Initialized LocalEmbedding with LM Studio: {self.lmstudio_url}")
    
    def _test_lmstudio(self) -> bool:
        """Test if LM Studio is available."""
        try:
            response = requests.get(f"{self.lmstudio_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding vector to unit length.
        
        Args:
            embedding: Raw embedding vector
            
        Returns:
            Normalized embedding vector
        """
        embedding_np = np.array(embedding)
        norm = np.linalg.norm(embedding_np)
        if norm > 0:
            normalized = embedding_np / norm
            return normalized.tolist()
        return embedding
    
    def _embed_with_lmstudio(self, text: str) -> List[float]:
        """Generate embedding using LM Studio."""
        try:
            response = requests.post(
                f"{self.lmstudio_url}/v1/embeddings",
                json={
                    "model": self.local_model,
                    "input": text
                },
                timeout=30
            )
            response.raise_for_status()
            embedding = response.json()["data"][0]["embedding"]
            return self._normalize_embedding(embedding)
        except Exception as e:
            error_logger.error(f"LM Studio embedding failed: {e}")
            raise
    
    def _embed_with_hf(self, text: str) -> List[float]:
        """Generate embedding using HuggingFace."""
        try:
            # Use feature extraction endpoint
            response = self.hf_client.feature_extraction(
                text=text,
                model=self.hf_model
            )
            # response is already a list of floats
            return self._normalize_embedding(response)
        except Exception as e:
            error_logger.error(f"HuggingFace embedding failed: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of normalized embedding vectors (768 dimensions each)
        """
        try:
            app_logger.info(f"Generating local embeddings for {len(texts)} chunks")
            embeddings = []
            
            for text in texts:
                if self.use_fallback:
                    embedding = self._embed_with_hf(text)
                else:
                    try:
                        embedding = self._embed_with_lmstudio(text)
                    except:
                        app_logger.warning("LM Studio failed, falling back to HuggingFace")
                        self.use_fallback = True
                        self.hf_client = InferenceClient(api_key=settings.hf_token)
                        embedding = self._embed_with_hf(text)
                
                embeddings.append(embedding)
            
            app_logger.info(f"Successfully generated {len(embeddings)} local embeddings")
            return embeddings
        except Exception as e:
            error_logger.error(f"Failed to generate local embeddings: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query.
        
        Args:
            text: Query text to embed
            
        Returns:
            Normalized embedding vector (768 dimensions)
        """
        try:
            app_logger.info("Generating local query embedding")
            
            if self.use_fallback:
                embedding = self._embed_with_hf(text)
            else:
                try:
                    embedding = self._embed_with_lmstudio(text)
                except:
                    app_logger.warning("LM Studio failed, falling back to HuggingFace")
                    self.use_fallback = True
                    self.hf_client = InferenceClient(api_key=settings.hf_token)
                    embedding = self._embed_with_hf(text)
            
            app_logger.info("Successfully generated local query embedding")
            return embedding
        except Exception as e:
            error_logger.error(f"Failed to generate local query embedding: {e}")
            raise
