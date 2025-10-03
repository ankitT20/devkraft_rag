"""
Qdrant vector storage service for managing document embeddings.
"""
import uuid
from typing import List, Dict, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class QdrantStorage:
    """
    Qdrant storage service managing both cloud and docker collections.
    """
    
    def __init__(self):
        """Initialize Qdrant clients for cloud and docker."""
        # Cloud client
        try:
            self.cloud_client = QdrantClient(
                url=settings.qdrant_cloud_url,
                api_key=settings.qdrant_api_key
            )
            self.cloud_collection = settings.qdrant_cloud_collection
            self._ensure_collection(
                self.cloud_client, 
                self.cloud_collection, 
                settings.gemini_embedding_dim
            )
            app_logger.info(f"Initialized Qdrant Cloud client: {settings.qdrant_cloud_url}")
        except Exception as e:
            error_logger.error(f"Failed to initialize Qdrant Cloud: {e}")
            raise
        
        # Docker client (optional, with fallback)
        self.docker_available = False
        try:
            self.docker_client = QdrantClient(url=settings.qdrant_docker_url)
            self.docker_collection = settings.qdrant_docker_collection
            self._ensure_collection(
                self.docker_client, 
                self.docker_collection, 
                settings.local_embedding_dim
            )
            self.docker_available = True
            app_logger.info(f"Initialized Qdrant Docker client: {settings.qdrant_docker_url}")
        except Exception as e:
            app_logger.warning(f"Qdrant Docker not available: {e}. Will use cloud only.")
    
    def _ensure_collection(self, client: QdrantClient, collection_name: str, vector_size: int):
        """
        Ensure collection exists, create if not.
        
        Args:
            client: Qdrant client
            collection_name: Name of the collection
            vector_size: Dimension of vectors
        """
        try:
            collections = client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if collection_name not in collection_names:
                app_logger.info(f"Creating collection: {collection_name} with vector size {vector_size}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                app_logger.info(f"Collection created: {collection_name}")
            else:
                app_logger.info(f"Collection already exists: {collection_name}")
        except Exception as e:
            error_logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise
    
    def store_embeddings_cloud(
        self, 
        embeddings: List[List[float]], 
        texts: List[str], 
        metadata: List[Dict] = None
    ) -> bool:
        """
        Store embeddings in Qdrant Cloud collection.
        
        Args:
            embeddings: List of embedding vectors
            texts: List of original texts
            metadata: Optional metadata for each text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            app_logger.info(f"Storing {len(embeddings)} embeddings in cloud collection")
            
            points = []
            for i, (embedding, text) in enumerate(zip(embeddings, texts)):
                point_id = str(uuid.uuid4())
                payload = {
                    "text": text,
                    "metadata": metadata[i] if metadata else {}
                }
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))
            
            self.cloud_client.upsert(
                collection_name=self.cloud_collection,
                points=points
            )
            
            app_logger.info(f"Successfully stored {len(points)} points in cloud collection")
            return True
            
        except Exception as e:
            error_logger.error(f"Failed to store embeddings in cloud: {e}")
            return False
    
    def store_embeddings_docker(
        self, 
        embeddings: List[List[float]], 
        texts: List[str], 
        metadata: List[Dict] = None
    ) -> bool:
        """
        Store embeddings in Qdrant Docker collection.
        
        Args:
            embeddings: List of embedding vectors
            texts: List of original texts
            metadata: Optional metadata for each text
            
        Returns:
            True if successful, False otherwise
        """
        if not self.docker_available:
            app_logger.warning("Docker not available, skipping docker storage")
            return False
        
        try:
            app_logger.info(f"Storing {len(embeddings)} embeddings in docker collection")
            
            points = []
            for i, (embedding, text) in enumerate(zip(embeddings, texts)):
                point_id = str(uuid.uuid4())
                payload = {
                    "text": text,
                    "metadata": metadata[i] if metadata else {}
                }
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                ))
            
            self.docker_client.upsert(
                collection_name=self.docker_collection,
                points=points
            )
            
            app_logger.info(f"Successfully stored {len(points)} points in docker collection")
            return True
            
        except Exception as e:
            error_logger.error(f"Failed to store embeddings in docker: {e}")
            return False
    
    def search_cloud(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        """
        Search for similar documents in cloud collection.
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            
        Returns:
            List of search results with text and metadata
        """
        try:
            app_logger.info(f"Searching cloud collection with limit={limit}")
            
            results = self.cloud_client.search(
                collection_name=self.cloud_collection,
                query_vector=query_vector,
                limit=limit
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "text": result.payload["text"],
                    "metadata": result.payload.get("metadata", {}),
                    "score": result.score
                })
            
            app_logger.info(f"Found {len(search_results)} results in cloud collection")
            return search_results
            
        except Exception as e:
            error_logger.error(f"Failed to search cloud collection: {e}")
            raise
    
    def search_docker(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        """
        Search for similar documents in docker collection.
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            
        Returns:
            List of search results with text and metadata
        """
        if not self.docker_available:
            app_logger.warning("Docker not available, returning empty results")
            return []
        
        try:
            app_logger.info(f"Searching docker collection with limit={limit}")
            
            results = self.docker_client.search(
                collection_name=self.docker_collection,
                query_vector=query_vector,
                limit=limit
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "text": result.payload["text"],
                    "metadata": result.payload.get("metadata", {}),
                    "score": result.score
                })
            
            app_logger.info(f"Found {len(search_results)} results in docker collection")
            return search_results
            
        except Exception as e:
            error_logger.error(f"Failed to search docker collection: {e}")
            raise
