"""
Document processing service for loading and chunking documents.
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    WebBaseLoader,
)
from langchain_experimental.text_splitter import SemanticChunker

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class DocumentProcessor:
    """
    Service for loading and chunking documents using LangChain.
    """

    def __init__(self, use_semantic_chunking: bool = False):
        """
        Initialize document processor with text splitter.

        Args:
            use_semantic_chunking: If True, use SemanticChunker. Requires embedding model.
        """
        self.use_semantic_chunking = use_semantic_chunking

        if use_semantic_chunking:
            # SemanticChunker requires an embedding function
            # We'll initialize it lazily when needed with the appropriate embedding model
            self.semantic_chunker = None
            app_logger.info("Initialized DocumentProcessor with SemanticChunker (lazy init)")
        else:
            # Use RecursiveCharacterTextSplitter as default
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""],
            )
            app_logger.info(
                f"Initialized DocumentProcessor with chunk_size={settings.chunk_size}, "
                f"chunk_overlap={settings.chunk_overlap}"
            )

    def _initialize_semantic_chunker(self):
        """Initialize SemanticChunker with embedding model."""
        if self.semantic_chunker is None:
            try:
                # Import here to avoid circular dependency
                from app.core.embeddings import GeminiEmbedding

                embedding = GeminiEmbedding()
                self.semantic_chunker = SemanticChunker(embedding.embeddings)
                app_logger.info("Initialized SemanticChunker with Gemini embeddings")
            except Exception as e:
                error_logger.error(f"Failed to initialize SemanticChunker: {e}")
                # Fallback to RecursiveCharacterTextSplitter
                self.use_semantic_chunking = False
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""],
                )
                app_logger.warning("Falling back to RecursiveCharacterTextSplitter")

    def preprocess_text(self, text: str) -> str:
        """
        Clean and standardize text by removing common noise patterns.

        Args:
            text: Raw text to preprocess

        Returns:
            Cleaned text
        """
        # Remove page numbers (common patterns)
        text = re.sub(r"\n\s*Page\s+\d+\s*\n", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)  # Standalone numbers on lines

        # Remove common header/footer patterns
        text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)  # "- 5 -" style page numbers

        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)  # Multiple newlines to double newline
        text = re.sub(r" {2,}", " ", text)  # Multiple spaces to single space

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    def load_document(self, file_path: str) -> Tuple[List[str], List[Dict]]:
        """
        Load and chunk a document based on its file type.

        Args:
            file_path: Path to the document file or URL (for websites)

        Returns:
            Tuple of (List of text chunks, List of chunk metadata with page/header info)
        """
        try:
            app_logger.info(f"Loading document: {file_path}")

            # Check if it's a URL (website)
            if file_path.startswith("http://") or file_path.startswith("https://"):
                return self._load_website(file_path)

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
            elif file_ext == ".csv":
                loader = CSVLoader(file_path, encoding="utf-8")
            else:
                # Try text loader as fallback
                app_logger.warning(f"Unknown file type {file_ext}, trying text loader")
                loader = TextLoader(file_path, encoding="utf-8")

            # Load documents
            documents = loader.load()

            # For PDFs, preserve page information
            if file_ext == ".pdf":
                chunks, chunk_metadata = self._process_pdf_with_metadata(documents, file_path)
            elif file_ext == ".csv":
                chunks, chunk_metadata = self._process_csv_with_metadata(documents, file_path)
            else:
                # For non-PDF documents, use simple chunking with preprocessing
                full_text = "\n\n".join([doc.page_content for doc in documents])
                # Apply preprocessing
                full_text = self.preprocess_text(full_text)
                chunks = self._chunk_text(full_text)
                chunk_metadata = []
                for i in range(len(chunks)):
                    chunk_metadata.append(
                        {
                            "page": 1,  # Default page for non-PDF
                            "header": Path(file_path).stem,  # Use filename as header
                        }
                    )

            app_logger.info(
                f"Successfully loaded and chunked document: {file_path} "
                f"into {len(chunks)} chunks"
            )
            return chunks, chunk_metadata

        except Exception as e:
            error_logger.error(f"Failed to load document {file_path}: {e}")
            raise

    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text using either semantic or recursive chunking.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if self.use_semantic_chunking:
            if self.semantic_chunker is None:
                self._initialize_semantic_chunker()
            if self.semantic_chunker is not None:
                return self.semantic_chunker.split_text(text)

        # Fallback to RecursiveCharacterTextSplitter
        return self.text_splitter.split_text(text)

    def _load_website(self, url: str) -> Tuple[List[str], List[Dict]]:
        """
        Load and chunk content from a website.

        Args:
            url: Website URL

        Returns:
            Tuple of (chunks, chunk_metadata)
        """
        try:
            app_logger.info(f"Loading website: {url}")
            loader = WebBaseLoader(url)
            documents = loader.load()

            # Combine all document content
            full_text = "\n\n".join([doc.page_content for doc in documents])

            # Apply preprocessing
            full_text = self.preprocess_text(full_text)

            # Chunk the text
            chunks = self._chunk_text(full_text)

            # Create metadata
            chunk_metadata = []
            for i in range(len(chunks)):
                chunk_metadata.append({"page": 1, "header": url})

            app_logger.info(f"Successfully loaded website {url} into {len(chunks)} chunks")
            return chunks, chunk_metadata

        except Exception as e:
            error_logger.error(f"Failed to load website {url}: {e}")
            raise

    def _process_csv_with_metadata(
        self, documents: List, file_path: str
    ) -> Tuple[List[str], List[Dict]]:
        """
        Process CSV documents with row information.

        Args:
            documents: List of loaded document rows
            file_path: Path to the document

        Returns:
            Tuple of (chunks, chunk_metadata)
        """
        all_chunks = []
        all_metadata = []

        # For CSV, each document is a row
        # Combine all rows into text, then chunk
        full_text = "\n\n".join([doc.page_content for doc in documents])

        # Apply preprocessing
        full_text = self.preprocess_text(full_text)

        # Chunk the text
        chunks = self._chunk_text(full_text)

        # Create metadata for each chunk
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({"page": 1, "header": Path(file_path).stem})

        return all_chunks, all_metadata

    def _process_pdf_with_metadata(
        self, documents: List, file_path: str
    ) -> Tuple[List[str], List[Dict]]:
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

            # Apply preprocessing to clean the content
            page_content = self.preprocess_text(page_content)

            # Extract header from first line or first 100 chars
            lines = page_content.split("\n")
            header = lines[0].strip() if lines else ""
            if len(header) > 100:
                header = header[:100] + "..."
            if not header:
                header = f"Page {page_num}"

            # Split page content into chunks
            page_chunks = self._chunk_text(page_content)

            # Associate each chunk with the page number and header
            for chunk in page_chunks:
                all_chunks.append(chunk)
                all_metadata.append({"page": page_num, "header": header})

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
        return {"filename": path.name}

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
