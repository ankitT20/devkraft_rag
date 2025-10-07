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
            
            # Load and chunk document (now returns chunks with per-chunk metadata and doc hash)
            chunks, chunk_specific_metadata, doc_hash = self.processor.load_document(file_path)
            
            # Get document-level metadata
            doc_metadata = self.processor.get_document_metadata(file_path)
            
            # Combine document-level and chunk-level metadata
            chunk_metadata = []
            for chunk_meta in chunk_specific_metadata:
                combined_meta = {**doc_metadata, **chunk_meta}
                chunk_metadata.append(combined_meta)
            
            # Generate embeddings and store
            cloud_success = False
            docker_success = False
            
            # Try Gemini + Cloud
            try:
                app_logger.info("Generating Gemini embeddings for cloud storage")
                gemini_embeddings = self.gemini_embedding.embed_documents(chunks)
                cloud_success = self.storage.store_embeddings_cloud(
                    gemini_embeddings, 
                    chunks, 
                    chunk_metadata,
                    doc_hash
                )
            except Exception as e:
                error_logger.error(f"Failed to store in cloud: {e}")
            
            # Try Local + Docker
            try:
                app_logger.info("Generating local embeddings for docker storage")
                local_embeddings = self.local_embedding.embed_documents(chunks)
                docker_success = self.storage.store_embeddings_docker(
                    local_embeddings, 
                    chunks, 
                    chunk_metadata,
                    doc_hash
                )
            except Exception as e:
                error_logger.error(f"Failed to store in docker: {e}")
            
            # Move file to appropriate folder
            destination = self._determine_destination(cloud_success, docker_success)
            self._move_file(file_path, destination)
            
            # Generate result message
            if cloud_success and docker_success:
                msg = f"Successfully ingested to both cloud and docker"
            elif cloud_success:
                msg = f"Successfully ingested to cloud only"
            elif docker_success:
                msg = f"Successfully ingested to docker only"
            else:
                msg = f"Failed to ingest to any database"
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
            if f.is_file() and f.suffix.lower() in ['.txt', '.pdf', '.docx', '.doc', '.md']
        ]
        
        app_logger.info(f"Found {len(files)} documents to ingest")
        
        for file_path in files:
            success, message = self.ingest_document(str(file_path))
            results.append((file_path.name, success, message))
        
        return results
