"""
Document processing service for loading and chunking documents.
"""
import os
from pathlib import Path
from typing import List, Dict, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class DocumentProcessor:
    """
    Service for loading and chunking documents using LangChain.
    """
    
    def __init__(self):
        """Initialize document processor with text splitter."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        app_logger.info(
            f"Initialized DocumentProcessor with chunk_size={settings.chunk_size}, "
            f"chunk_overlap={settings.chunk_overlap}"
        )
    
    def load_document(self, file_path: str) -> Tuple[List[str], List[Dict]]:
        """
        Load and chunk a document based on its file type.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (List of text chunks, List of metadata dicts for each chunk)
        """
        try:
            app_logger.info(f"Loading document: {file_path}")
            file_ext = Path(file_path).suffix.lower()
            
            # Select appropriate loader
            if file_ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
            elif file_ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_ext in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            elif file_ext == ".md":
                loader = UnstructuredMarkdownLoader(file_path)
            else:
                # Try text loader as fallback
                app_logger.warning(f"Unknown file type {file_ext}, trying text loader")
                loader = TextLoader(file_path, encoding="utf-8")
            
            # Load documents
            documents = loader.load()
            
            # For PDFs, we want to preserve page information
            # Split into chunks while preserving metadata
            chunks = []
            chunk_metadata = []
            
            for doc in documents:
                # Extract page number from metadata if available
                page_num = doc.metadata.get('page', None)
                if page_num is not None:
                    page_num = page_num + 1  # Convert 0-indexed to 1-indexed
                
                # Extract header/title from first line of content
                content_lines = doc.page_content.strip().split('\n')
                header = content_lines[0][:100] if content_lines else ""  # First 100 chars as header
                
                # Split this document into chunks
                doc_chunks = self.text_splitter.split_text(doc.page_content)
                
                for chunk in doc_chunks:
                    chunks.append(chunk)
                    # Store metadata for each chunk
                    chunk_meta = {
                        'page': page_num,
                        'header': header.strip(),
                        'source': doc.metadata.get('source', file_path)
                    }
                    chunk_metadata.append(chunk_meta)
            
            app_logger.info(
                f"Successfully loaded and chunked document: {file_path} "
                f"into {len(chunks)} chunks"
            )
            return chunks, chunk_metadata
            
        except Exception as e:
            error_logger.error(f"Failed to load document {file_path}: {e}")
            raise
    
    def get_document_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)
        return {
            "filename": path.name,
            "file_type": path.suffix,
            "file_size": path.stat().st_size,
            "file_path": str(path)
        }
