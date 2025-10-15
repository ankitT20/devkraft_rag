"""
Document ingestion service for processing and storing documents in vector databases.
"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple

from app.config import settings
from app.core.embeddings import GeminiEmbedding, LocalEmbedding
from app.core.storage import QdrantStorage
from app.services.document_processor import DocumentProcessor
from app.utils.logging_config import app_logger, error_logger


class IngestionService:
    """
    Service for ingesting documents into vector databases.
    Processes documents, generates embeddings, and stores in both cloud and docker.
    """
    
    def __init__(self):
        """Initialize ingestion service with all required components."""
        self.gemini_embedding = GeminiEmbedding()
        self.local_embedding = LocalEmbedding()
        self.storage = QdrantStorage()
        self.processor = DocumentProcessor()
        
        # Ensure output folders exist
        self._ensure_folders()
        
        app_logger.info("Initialized IngestionService")
    
    def _ensure_folders(self):
        """Create output folders if they don't exist."""
        folders = [
            settings.stored_folder,
            settings.stored_docker_only_folder,
            settings.stored_cloud_only_folder
        ]
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
    
    def ingest_document(self, file_path: str) -> Tuple[bool, str]:
        """
        Ingest a single document into vector databases.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            app_logger.info(f"Starting ingestion for: {file_path}")
            
            # Calculate MD5 hash for the document
            md5_hash = self.processor.calculate_md5(file_path)
            app_logger.info(f"Document MD5: {md5_hash}")
            
            # Check if document already exists BEFORE processing to save API quota
            cloud_exists = self.storage.check_document_exists(md5_hash, settings.qdrant_cloud_collection)
            docker_exists = self.storage.check_document_exists(md5_hash, settings.qdrant_docker_collection)
            
            if cloud_exists or docker_exists:
                # Provide specific message about where the document exists
                if cloud_exists and docker_exists:
                    msg = "duplicate: document already exists in both cloud and docker storage"
                    self._move_file(file_path, settings.stored_folder)
                elif cloud_exists:
                    msg = "duplicate: document already exists in cloud storage"
                    self._move_file(file_path, settings.stored_cloud_only_folder)
                elif docker_exists:
                    msg = "duplicate: document already exists in docker storage"
                    self._move_file(file_path, settings.stored_docker_only_folder)
                
                app_logger.info(f"Document with MD5 {md5_hash} already exists - skipping processing")
                return False, msg
            
            # Load and chunk document with metadata
            try:
                chunks, chunk_page_metadata = self.processor.load_document(file_path)
            except ValueError as ve:
                # Specific error from document processor about empty content
                msg = f"empty content: {str(ve)}"
                error_logger.error(f"Document {file_path} has no content: {ve}")
                return False, msg
            except Exception as e:
                # Other loading errors
                msg = f"loading error: {str(e)}"
                error_logger.error(f"Failed to load document {file_path}: {e}")
                return False, msg
            
            # Validate that we have chunks to process
            if not chunks or len(chunks) == 0:
                msg = "empty content: document resulted in 0 chunks after processing"
                error_logger.error(f"Document {file_path} resulted in 0 chunks after processing")
                return False, msg
            
            base_metadata = self.processor.get_document_metadata(file_path)
            
            # Prepare metadata for each chunk with page, header, and chunkno
            chunk_metadata = []
            for i, page_meta in enumerate(chunk_page_metadata):
                chunk_meta = {
                    **base_metadata,
                    "page": page_meta["page"],
                    "header": page_meta["header"],
                    "chunkno": i + 1  # Integer chunk number starting from 1
                }
                chunk_metadata.append(chunk_meta)
            
            # Generate embeddings and store
            cloud_success = False
            docker_success = False
            
            # Try Gemini + Cloud
            cloud_error = None
            try:
                app_logger.info("Generating Gemini embeddings for cloud storage")
                gemini_embeddings = self.gemini_embedding.embed_documents(chunks)
                cloud_success = self.storage.store_embeddings_cloud(
                    gemini_embeddings, 
                    chunks, 
                    chunk_metadata,
                    md5_hash=md5_hash
                )
            except Exception as e:
                cloud_error = str(e)
                error_logger.error(f"Failed to store in cloud: {e}")
            
            # Try Local + Docker
            docker_error = None
            try:
                app_logger.info("Generating local embeddings for docker storage")
                local_embeddings = self.local_embedding.embed_documents(chunks)
                docker_success = self.storage.store_embeddings_docker(
                    local_embeddings, 
                    chunks, 
                    chunk_metadata,
                    md5_hash=md5_hash
                )
            except Exception as e:
                docker_error = str(e)
                error_logger.error(f"Failed to store in docker: {e}")
            
            # Move file to appropriate folder
            destination = self._determine_destination(cloud_success, docker_success)
            self._move_file(file_path, destination)
            
            # Generate result message
            if cloud_success and docker_success:
                msg = "✅Success: ingested to both cloud and docker"
            elif cloud_success:
                msg = "✅Success: ingested to cloud only"
                # if docker_error:
                #     msg += f" (docker failed: {docker_error[:100]})"
            elif docker_success:
                msg = "partial Success: ingested to docker only"
                if cloud_error:
                    msg += f" (cloud failed: {cloud_error[:100]})"
            else:
                # Both failed - provide detailed error message
                errors = []
                if cloud_error:
                    # Check for specific error types
                    if "INVALID_ARGUMENT" in cloud_error and "empty" in cloud_error.lower():
                        errors.append("cloud embedding error: batch request was empty")
                    elif "INVALID_ARGUMENT" in cloud_error and "100" in cloud_error:
                        errors.append("cloud embedding error: exceeded batch size limit")
                    else:
                        errors.append(f"cloud error: {cloud_error[:100]}")
                if docker_error:
                    if "402" in docker_error or "Payment Required" in docker_error:
                        errors.append("docker error: HuggingFace quota exceeded")
                    else:
                        errors.append(f"docker error: {docker_error[:100]}")
                
                msg = "failed: " + "; ".join(errors) if errors else "failed: unknown error"
                error_logger.error(msg)
                return False, msg
            
            app_logger.info(msg)
            return True, msg
            
        except Exception as e:
            error_logger.error(f"Failed to ingest document {file_path}: {e}")
            return False, f"Error: {str(e)}"
    
    def _determine_destination(self, cloud_success: bool, docker_success: bool) -> str:
        """
        Determine destination folder based on storage success.
        
        Args:
            cloud_success: Whether cloud storage succeeded
            docker_success: Whether docker storage succeeded
            
        Returns:
            Destination folder path
        """
        if cloud_success and docker_success:
            return settings.stored_folder
        elif cloud_success:
            return settings.stored_cloud_only_folder
        elif docker_success:
            return settings.stored_docker_only_folder
        else:
            # Keep in generate_embeddings if both failed
            return settings.generate_embeddings_folder
    
    def _move_file(self, source: str, destination_folder: str):
        """
        Move file to destination folder.
        
        Args:
            source: Source file path
            destination_folder: Destination folder path
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination_folder) / source_path.name
            
            # If destination exists, add a number
            counter = 1
            while dest_path.exists():
                dest_path = Path(destination_folder) / f"{source_path.stem}_{counter}{source_path.suffix}"
                counter += 1
            
            shutil.move(str(source_path), str(dest_path))
            app_logger.info(f"Moved file from {source} to {dest_path}")
            
        except Exception as e:
            error_logger.error(f"Failed to move file {source}: {e}")
    
    def ingest_all_documents(self) -> List[Tuple[str, bool, str]]:
        """
        Ingest all documents in the generate_embeddings folder.
        
        Returns:
            List of tuples (filename, success, message)
        """
        results = []
        folder = Path(settings.generate_embeddings_folder)
        
        # Get all files (not in subdirectories)
        files = [
            f for f in folder.iterdir() 
            if f.is_file() and f.suffix.lower() in ['.txt', '.pdf', '.docx', '.doc', '.md', '.csv']
        ]
        
        app_logger.info(f"Found {len(files)} documents to ingest")
        
        for file_path in files:
            success, message = self.ingest_document(str(file_path))
            results.append((file_path.name, success, message))
        
        return results
    
    def ingest_website(self, url: str) -> Tuple[bool, str]:
        """
        Ingest content from a website into vector databases.
        
        Args:
            url: Website URL to ingest
            
        Returns:
            Tuple of (success, message)
        """
        try:
            app_logger.info(f"Starting ingestion for website: {url}")
            
            # Load and chunk website content
            chunks, chunk_page_metadata = self.processor.load_website(url)
            base_metadata = {"filename": url}
            
            # Prepare metadata for each chunk
            chunk_metadata = []
            for i, page_meta in enumerate(chunk_page_metadata):
                chunk_meta = {
                    **base_metadata,
                    "page": page_meta.get("page", 1),
                    "header": page_meta.get("header", f"Web: {url}"),
                    "chunkno": i + 1,
                    "source": page_meta.get("source", url)
                }
                chunk_metadata.append(chunk_meta)
            
            # Generate embeddings and store
            cloud_success = False
            docker_success = False
            
            # Try cloud storage with Gemini embeddings
            try:
                gemini_vectors = self.gemini_embedding.embed_documents(chunks)
                self.storage.add_to_cloud(gemini_vectors, chunk_metadata)
                cloud_success = True
                app_logger.info(f"Successfully stored website in cloud: {url}")
            except Exception as e:
                error_logger.error(f"Failed to store website in cloud: {e}")
            
            # Try docker storage with local embeddings
            try:
                local_vectors = self.local_embedding.embed_documents(chunks)
                self.storage.add_to_docker(local_vectors, chunk_metadata)
                docker_success = True
                app_logger.info(f"Successfully stored website in docker: {url}")
            except Exception as e:
                error_logger.error(f"Failed to store website in docker: {e}")
            
            # Determine success message
            if cloud_success and docker_success:
                message = "Successfully ingested website into both cloud and docker"
            elif cloud_success:
                message = "Successfully ingested website into cloud only"
            elif docker_success:
                message = "Successfully ingested website into docker only"
            else:
                message = "Failed to ingest website into any storage"
            
            success = cloud_success or docker_success
            app_logger.info(f"Website ingestion completed: {url} - {message}")
            
            return success, message
            
        except Exception as e:
            error_logger.error(f"Failed to ingest website {url}: {e}")
            return False, f"Error: {str(e)}"
