"""
Document processing service for loading and chunking documents.
"""
import os
import hashlib
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
            Tuple of (List of text chunks, List of chunk metadata with page/header info)
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
            
            # For PDFs, preserve page information
            if file_ext == ".pdf":
                chunks, chunk_metadata = self._process_pdf_with_metadata(documents, file_path)
            else:
                # For non-PDF documents, use simple chunking
                full_text = "\n\n".join([doc.page_content for doc in documents])
                chunks = self.text_splitter.split_text(full_text)
                chunk_metadata = []
                for i in range(len(chunks)):
                    chunk_metadata.append({
                        "page": 1,  # Default page for non-PDF
                        "header": Path(file_path).stem  # Use filename as header
                    })
            
            app_logger.info(
                f"Successfully loaded and chunked document: {file_path} "
                f"into {len(chunks)} chunks"
            )
            return chunks, chunk_metadata
            
        except Exception as e:
            error_logger.error(f"Failed to load document {file_path}: {e}")
            raise
    
    def _process_pdf_with_metadata(self, documents: List, file_path: str) -> Tuple[List[str], List[Dict]]:
        """
        Process PDF documents preserving page numbers and extracting headers.
        
        Args:
            documents: List of loaded document pages
            file_path: Path to the document
            
        Returns:
            Tuple of (chunks, chunk_metadata)
        """
        all_chunks = []
        all_metadata = []
        
        for doc in documents:
            page_num = doc.metadata.get("page", 0) + 1  # PyPDFLoader uses 0-based indexing
            page_content = doc.page_content
            
            # Extract header from first line or first 100 chars
            lines = page_content.split('\n')
            header = lines[0].strip() if lines else ""
            if len(header) > 100:
                header = header[:100] + "..."
            if not header:
                header = f"Page {page_num}"
            
            # Split page content into chunks
            page_chunks = self.text_splitter.split_text(page_content)
            
            # Associate each chunk with the page number and header
            for chunk in page_chunks:
                all_chunks.append(chunk)
                all_metadata.append({
                    "page": page_num,
                    "header": header
                })
        
        return all_chunks, all_metadata
    
    def get_document_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from a document including MD5 hash.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary of metadata (filename only)
        """
        path = Path(file_path)
        return {
            "filename": path.name
        }
    
    def calculate_md5(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash as hex string
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest().upper()
