"""
Document processing service for loading and chunking documents.
"""
import os
from pathlib import Path
from typing import List, Dict
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
    
    def load_document(self, file_path: str) -> List[str]:
        """
        Load and chunk a document based on its file type.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of text chunks
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
            
            # Combine all document content
            full_text = "\n\n".join([doc.page_content for doc in documents])
            
            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            app_logger.info(
                f"Successfully loaded and chunked document: {file_path} "
                f"into {len(chunks)} chunks"
            )
            return chunks
            
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
