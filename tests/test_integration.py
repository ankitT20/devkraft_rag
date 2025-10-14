"""
Integration tests for document ingestion with various file types.
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.services.document_processor import DocumentProcessor


class TestIntegrationDocumentProcessing:
    """Integration tests for document processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()

    def test_csv_integration(self):
        """Integration test for CSV file processing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("id,name,description\n")
            f.write("1,Product A,High quality product for testing\n")
            f.write("2,Product B,Another excellent product\n")
            f.write("3,Product C,Third product for variety\n")
            csv_file = f.name

        try:
            chunks, metadata = self.processor.load_document(csv_file)
            assert len(chunks) > 0, "Should have chunks"
            assert len(metadata) == len(chunks), "Metadata should match chunks"

            # Verify preprocessing worked
            combined_text = " ".join(chunks)
            assert "Product" in combined_text, "Should contain CSV content"

            # Verify metadata structure
            for meta in metadata:
                assert "page" in meta
                assert "header" in meta
                assert meta["page"] == 1  # CSV files should be single page

        finally:
            os.unlink(csv_file)

    def test_markdown_with_preprocessing(self):
        """Test markdown file with preprocessing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            # Add some content with noise that should be cleaned
            f.write("# Main Title\n\n")
            f.write("This is the content of the markdown.\n\n")
            f.write("Page 5\n\n")  # Should be removed
            f.write("More content here.\n\n")
            f.write("- 10 -\n\n")  # Should be removed
            f.write("Final paragraph.\n")
            md_file = f.name

        try:
            chunks, metadata = self.processor.load_document(md_file)
            assert len(chunks) > 0

            # Check that preprocessing removed page numbers
            combined_text = " ".join(chunks)
            assert "Main Title" in combined_text
            assert "More content here" in combined_text

        finally:
            os.unlink(md_file)

    def test_text_file_with_long_content(self):
        """Test text file with content requiring chunking."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            # Create long content
            for i in range(200):
                f.write(
                    f"Paragraph {i}: This is a long paragraph with sufficient "
                    f"content to test chunking behavior. "
                    f"It contains multiple sentences to ensure proper splitting.\n\n"
                )
            text_file = f.name

        try:
            chunks, metadata = self.processor.load_document(text_file)
            assert len(chunks) > 1, "Long file should produce multiple chunks"
            assert len(metadata) == len(chunks)

            # Verify all metadata has required fields
            for meta in metadata:
                assert "page" in meta
                assert "header" in meta

        finally:
            os.unlink(text_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
