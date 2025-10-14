"""
Tests for document processor with new loaders and preprocessing.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()

    def test_preprocess_text_removes_page_numbers(self):
        """Test that preprocessing removes page numbers."""
        text = """Some content here
Page 5
More content here
- 10 -
Even more content"""
        result = self.processor.preprocess_text(text)
        assert "Page 5" not in result
        assert "- 10 -" not in result
        assert "Some content here" in result
        assert "More content here" in result

    def test_preprocess_text_removes_excessive_whitespace(self):
        """Test that preprocessing removes excessive whitespace."""
        text = "Line 1\n\n\n\nLine 2    multiple    spaces"
        result = self.processor.preprocess_text(text)
        assert "\n\n\n\n" not in result
        assert "    " not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_load_csv_document(self):
        """Test loading CSV files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("name,age,city\n")
            f.write("John,30,NYC\n")
            f.write("Jane,25,LA\n")
            csv_file = f.name

        try:
            chunks, metadata = self.processor.load_document(csv_file)
            assert len(chunks) > 0
            assert len(metadata) == len(chunks)
            # Check that CSV content is in the chunks
            full_text = " ".join(chunks)
            assert "John" in full_text or "Jane" in full_text
        finally:
            os.unlink(csv_file)

    def test_load_text_document(self):
        """Test loading text files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("This is a test document.\n" * 100)
            text_file = f.name

        try:
            chunks, metadata = self.processor.load_document(text_file)
            assert len(chunks) > 0
            assert len(metadata) == len(chunks)
            assert "This is a test document" in chunks[0]
        finally:
            os.unlink(text_file)

    def test_chunk_text_with_recursive_splitter(self):
        """Test chunking with RecursiveCharacterTextSplitter."""
        text = "A" * 10000  # Long text
        chunks = self.processor._chunk_text(text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= self.processor.text_splitter._chunk_size + 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
