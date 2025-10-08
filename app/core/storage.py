"""
Qdrant vector storage service for managing document embeddings.
"""
import uuid
from uuid_extensions import uuid7, uuid_to_datetime
from typing import List, Dict, Tuple
from datetime import datetime, timezone
import struct
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue,
    PayloadSchemaType, PayloadIndexInfo
)

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class QdrantStorage:
    """
    Qdrant storage service managing both cloud and docker collections.
    """
    
    def __init__(self):
        """Initialize Qdrant clients for cloud and docker."""
        # Cloud client - always required
        try:
            self.cloud_client = QdrantClient(
                url=settings.qdrant_cloud_url,
                api_key=settings.qdrant_api_key
            )
            
            # Ensure both collections exist in cloud
            self.cloud_collection = settings.qdrant_cloud_collection
            self.cloud_docker_collection = settings.qdrant_docker_collection
            
            self._ensure_collection(
                self.cloud_client, 
                self.cloud_collection, 
                settings.gemini_embedding_dim
            )
            self._ensure_collection(
                self.cloud_client, 
                self.cloud_docker_collection, 
                settings.local_embedding_dim
            )
            app_logger.info(f"Initialized Qdrant Cloud client: {settings.qdrant_cloud_url}")
            app_logger.info(f"Cloud collections: {self.cloud_collection}, {self.cloud_docker_collection}")
        except Exception as e:
            error_logger.error(f"Failed to initialize Qdrant Cloud: {e}")
            raise
        
        # Docker client (optional, with cloud fallback)
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
            app_logger.warning(f"Qdrant Docker not available: {e}. Will use cloud fallback.")
    
    def _ensure_collection(self, client: QdrantClient, collection_name: str, vector_size: int):
        """
        Ensure collection exists, create if not. Also creates payload indexes for searchable fields.
        
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
            
            # Create payload indexes for md5 (keyword) and chunkno (integer)
            self._ensure_payload_indexes(client, collection_name)
            
        except Exception as e:
            error_logger.error(f"Failed to ensure collection {collection_name}: {e}")
            raise
    
    def _ensure_payload_indexes(self, client: QdrantClient, collection_name: str):
        """
        Ensure payload indexes exist for md5 and chunkno fields.
        
        Args:
            client: Qdrant client
            collection_name: Name of the collection
        """
        try:
            # Create index for md5 field (keyword type for exact matching)
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="md5",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                app_logger.info(f"Created md5 keyword index for {collection_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    app_logger.info(f"md5 index already exists for {collection_name}")
                else:
                    app_logger.warning(f"Could not create md5 index: {e}")
            
            # Create index for chunkno field (integer type)
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="metadata.chunkno",
                    field_schema=PayloadSchemaType.INTEGER
                )
                app_logger.info(f"Created chunkno integer index for {collection_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    app_logger.info(f"chunkno index already exists for {collection_name}")
                else:
                    app_logger.warning(f"Could not create chunkno index: {e}")
                    
        except Exception as e:
            error_logger.error(f"Failed to ensure payload indexes for {collection_name}: {e}")
            # Don't raise - indexes are optional optimization
    
    def check_document_exists(self, md5_hash: str, collection_name: str = None) -> bool:
        """
        Check if a document with the given MD5 hash already exists in the collection.
        
        Args:
            md5_hash: MD5 hash of the document
            collection_name: Optional collection name (defaults to cloud collection)
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            if collection_name is None:
                collection_name = self.cloud_collection
            
            # Search for documents with this MD5
            results = self.cloud_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="md5",
                            match=MatchValue(value=md5_hash)
                        )
                    ]
                ),
                limit=1
            )
            
            exists = len(results[0]) > 0
            if exists:
                app_logger.info(f"Document with MD5 {md5_hash} already exists in {collection_name}")
            return exists
            
        except Exception as e:
            error_logger.error(f"Failed to check document existence: {e}")
            return False
    
    def store_embeddings_cloud(
        self, 
        embeddings: List[List[float]], 
        texts: List[str], 
        metadata: List[Dict] = None,
        md5_hash: str = None
    ) -> bool:
        """
        Store embeddings in Qdrant Cloud collection.
        
        Args:
            embeddings: List of embedding vectors
            texts: List of original texts
            metadata: Optional metadata for each text
            md5_hash: MD5 hash of the source document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if document already exists
            if md5_hash and self.check_document_exists(md5_hash, self.cloud_collection):
                app_logger.info(f"Skipping document with MD5 {md5_hash} - already exists")
                return False
            
            app_logger.info(f"Storing {len(embeddings)} embeddings in cloud collection")
            
            points = []
            for i, (embedding, text) in enumerate(zip(embeddings, texts)):
                point_id = str(uuid7())  # Use UUIDv7 for monotonic growth
                payload = {
                    "text": text,
                    "md5": md5_hash,
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
        metadata: List[Dict] = None,
        md5_hash: str = None
    ) -> bool:
        """
        Store embeddings in Qdrant Docker collection with cloud replication.
        Stores in both Docker (if available) and Cloud for redundancy.
        
        Args:
            embeddings: List of embedding vectors
            texts: List of original texts
            metadata: Optional metadata for each text
            md5_hash: MD5 hash of the source document
            
        Returns:
            True if at least one storage succeeded, False otherwise
        """
        # Check if document already exists
        if md5_hash and self.check_document_exists(md5_hash, self.cloud_docker_collection):
            app_logger.info(f"Skipping document with MD5 {md5_hash} - already exists")
            return False
        
        docker_success = False
        cloud_success = False
        
        # Prepare points
        points = []
        for i, (embedding, text) in enumerate(zip(embeddings, texts)):
            point_id = str(uuid7())  # Use UUIDv7 for monotonic growth
            payload = {
                "text": text,
                "md5": md5_hash,
                "metadata": metadata[i] if metadata else {}
            }
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        # Try storing in Docker first
        if self.docker_available:
            try:
                app_logger.info(f"Storing {len(embeddings)} embeddings in docker collection (localhost)")
                self.docker_client.upsert(
                    collection_name=self.docker_collection,
                    points=points
                )
                app_logger.info(f"Successfully stored {len(points)} points in docker collection (localhost)")
                docker_success = True
            except Exception as e:
                error_logger.error(f"Failed to store embeddings in docker: {e}")
        else:
            app_logger.info("Docker not available, skipping localhost storage")
        
        # Always replicate to cloud (bootcamp_rag_docker collection)
        try:
            app_logger.info(f"Replicating {len(embeddings)} embeddings to cloud docker collection")
            self.cloud_client.upsert(
                collection_name=self.cloud_docker_collection,
                points=points
            )
            app_logger.info(f"Successfully replicated {len(points)} points to cloud docker collection")
            cloud_success = True
        except Exception as e:
            error_logger.error(f"Failed to replicate embeddings to cloud docker collection: {e}")
        
        return docker_success or cloud_success
    
    def search_cloud(self, query_vector: List[float], limit: int = 4) -> List[Dict]:
        """
        Search for similar documents in cloud collection.
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            
        Returns:
            List of search results with text, metadata, md5, and score
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
                    "md5": result.payload.get("md5", ""),
                    "score": result.score,
                    "id": str(result.id)
                })
            
            app_logger.info(f"Found {len(search_results)} results in cloud collection")
            return search_results
            
        except Exception as e:
            error_logger.error(f"Failed to search cloud collection: {e}")
            raise
    
    def search_docker(self, query_vector: List[float], limit: int = 4) -> List[Dict]:
        """
        Search for similar documents in docker collection with cloud fallback.
        First tries Docker localhost, then falls back to cloud docker collection.
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            
        Returns:
            List of search results with text and metadata
        """
        # Try Docker localhost first
        if self.docker_available:
            try:
                app_logger.info(f"Searching docker collection (localhost) with limit={limit}")
                
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
                        "md5": result.payload.get("md5", ""),
                        "score": result.score,
                        "id": str(result.id)
                    })
                
                app_logger.info(f"Found {len(search_results)} results in docker collection (localhost)")
                return search_results
                
            except Exception as e:
                error_logger.error(f"Failed to search docker localhost: {e}, falling back to cloud")
        else:
            app_logger.info("Docker not available, using cloud fallback")
        
        # Fallback to cloud docker collection
        try:
            app_logger.info(f"Searching cloud docker collection with limit={limit}")
            
            results = self.cloud_client.search(
                collection_name=self.cloud_docker_collection,
                query_vector=query_vector,
                limit=limit
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "text": result.payload["text"],
                    "metadata": result.payload.get("metadata", {}),
                    "md5": result.payload.get("md5", ""),
                    "score": result.score,
                    "id": str(result.id)
                })
            
            app_logger.info(f"Found {len(search_results)} results in cloud docker collection")
            return search_results
            
        except Exception as e:
            error_logger.error(f"Failed to search cloud docker collection: {e}")
            raise
    
    # ===================================================================
    # Commented out utility functions as per requirements - not needed for now
    # These functions can query documents by MD5 and chunkno, and decode UUIDv7 timestamps
    # ===================================================================
    #
    # def get_max_chunkno_by_md5(self, md5_hash: str, collection_name: str = None) -> int:
    #     """
    #     Get the maximum chunk number for a document by MD5 hash.
    #     This gives you the total number of chunks for that document.
    #     
    #     Args:
    #         md5_hash: MD5 hash of the document
    #         collection_name: Optional collection name (defaults to cloud collection)
    #         
    #     Returns:
    #         Maximum chunk number (integer), or 0 if document not found
    #     """
    #     try:
    #         if collection_name is None:
    #             collection_name = self.cloud_collection
    #         
    #         # Scroll through all points with this MD5 to find the maximum chunkno
    #         results, _ = self.cloud_client.scroll(
    #             collection_name=collection_name,
    #             scroll_filter=Filter(
    #                 must=[
    #                     FieldCondition(
    #                         key="md5",
    #                         match=MatchValue(value=md5_hash)
    #                     )
    #                 ]
    #             ),
    #             limit=1000,  # Adjust if you have more chunks per document
    #             with_payload=True
    #         )
    #         
    #         if not results:
    #             app_logger.info(f"No document found with MD5: {md5_hash}")
    #             return 0
    #         
    #         max_chunkno = 0
    #         for point in results:
    #             chunkno = point.payload.get("metadata", {}).get("chunkno", 0)
    #             if isinstance(chunkno, int) and chunkno > max_chunkno:
    #                 max_chunkno = chunkno
    #         
    #         app_logger.info(f"Document {md5_hash} has max chunkno: {max_chunkno}")
    #         return max_chunkno
    #         
    #     except Exception as e:
    #         error_logger.error(f"Failed to get max chunkno for MD5 {md5_hash}: {e}")
    #         return 0
    # 
    # def get_point_by_md5_and_chunkno(self, md5_hash: str, chunkno: int, collection_name: str = None) -> str:
    #     """
    #     Get the point UUID by filtering on MD5 and chunk number.
    #     
    #     Args:
    #         md5_hash: MD5 hash of the document
    #         chunkno: Chunk number (integer)
    #         collection_name: Optional collection name (defaults to cloud collection)
    #         
    #     Returns:
    #         Point UUID as string, or empty string if not found
    #     """
    #     try:
    #         if collection_name is None:
    #             collection_name = self.cloud_collection
    #         
    #         # Search for the specific point with MD5 and chunkno
    #         results, _ = self.cloud_client.scroll(
    #             collection_name=collection_name,
    #             scroll_filter=Filter(
    #                 must=[
    #                     FieldCondition(
    #                         key="md5",
    #                         match=MatchValue(value=md5_hash)
    #                     ),
    #                     FieldCondition(
    #                         key="metadata.chunkno",
    #                         match=MatchValue(value=chunkno)
    #                     )
    #                 ]
    #             ),
    #             limit=1,
    #             with_payload=True
    #         )
    #         
    #         if results:
    #             point_id = str(results[0].id)
    #             app_logger.info(f"Found point {point_id} for MD5 {md5_hash}, chunkno {chunkno}")
    #             return point_id
    #         else:
    #             app_logger.info(f"No point found for MD5 {md5_hash}, chunkno {chunkno}")
    #             return ""
    #             
    #     except Exception as e:
    #         error_logger.error(f"Failed to get point by MD5 and chunkno: {e}")
    #         return ""
    # 
    # def decode_uuid7(self, uuid_string: str) -> datetime:
    #     """
    #     Decode a UUIDv7 (uuid_extensions format) to readable timestamp.
    #     Uses the uuid_to_datetime function from uuid_extensions package.
    #     
    #     Args:
    #         uuid_string: UUID string to decode
    #         
    #     Returns:
    #         datetime object in UTC timezone
    #     """
    #     try:
    #         # Convert to UUID object if needed
    #         if isinstance(uuid_string, str):
    #             u = uuid.UUID(uuid_string)
    #         else:
    #             u = uuid_string
    #         
    #         # Use uuid_extensions built-in function to decode
    #         dt = uuid_to_datetime(u)
    #         
    #         app_logger.info(f"Decoded UUID {uuid_string} to timestamp: {dt}")
    #         return dt
    #         
    #     except Exception as e:
    #         error_logger.error(f"Failed to decode UUID7 {uuid_string}: {e}")
    #         raise
