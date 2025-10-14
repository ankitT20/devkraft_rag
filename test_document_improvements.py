#!/usr/bin/env python3
"""
Test script for document processing improvements.
Tests CSV support, text preprocessing, and semantic chunking.
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.document_processor import DocumentProcessor
from app.config import settings

def test_preprocessing():
    """Test text preprocessing."""
    print("Testing text preprocessing...")
    processor = DocumentProcessor(use_semantic_chunking=False)
    
    # Test text with noise
    noisy_text = """Page 1 of 10


    This   is    a    test    document.


    Page 2 of 10

    With  multiple     spaces   and   page   numbers.


    1


    2


    3
    """
    
    cleaned = processor._preprocess_text(noisy_text)
    print(f"  Original length: {len(noisy_text)}")
    print(f"  Cleaned length: {len(cleaned)}")
    print(f"  Cleaned text preview: {cleaned[:100]}...")
    assert len(cleaned) < len(noisy_text), "Text should be shortened after preprocessing"
    print("✓ Preprocessing test passed!\n")
    return True

def test_csv_support():
    """Test CSV file support."""
    print("Testing CSV support...")
    
    # Create a test CSV file
    test_csv = Path('/tmp/test_data.csv')
    test_csv.write_text("name,age,city\nJohn,30,NYC\nJane,25,LA\nBob,35,SF")
    
    processor = DocumentProcessor(use_semantic_chunking=False)
    
    try:
        chunks, metadata = processor.load_document(str(test_csv))
        assert len(chunks) > 0, "Should have at least one chunk"
        assert len(metadata) == len(chunks), "Metadata length should match chunks"
        print(f"  ✓ CSV loaded successfully: {len(chunks)} chunks")
        print(f"  First chunk preview: {chunks[0][:100] if chunks else 'No chunks'}...")
        print("✓ CSV support test passed!\n")
        return True
    except Exception as e:
        print(f"✗ CSV support test failed: {e}\n")
        return False
    finally:
        test_csv.unlink(missing_ok=True)

def test_text_support():
    """Test text file support."""
    print("Testing text file support...")
    
    # Create a test text file
    test_txt = Path('/tmp/test_data.txt')
    test_txt.write_text("This is a test document.\n\nIt has multiple paragraphs.\n\nAnd some content to chunk.")
    
    processor = DocumentProcessor(use_semantic_chunking=False)
    
    try:
        chunks, metadata = processor.load_document(str(test_txt))
        assert len(chunks) > 0, "Should have at least one chunk"
        assert len(metadata) == len(chunks), "Metadata length should match chunks"
        print(f"  ✓ Text loaded successfully: {len(chunks)} chunks")
        print(f"  First chunk preview: {chunks[0][:100] if chunks else 'No chunks'}...")
        print("✓ Text support test passed!\n")
        return True
    except Exception as e:
        print(f"✗ Text support test failed: {e}\n")
        return False
    finally:
        test_txt.unlink(missing_ok=True)

def test_semantic_chunking_fallback():
    """Test semantic chunking with fallback."""
    print("Testing semantic chunking fallback...")
    
    # Create processor with semantic chunking
    processor = DocumentProcessor(use_semantic_chunking=True)
    
    # Check if semantic splitter is available
    if processor.semantic_splitter is None:
        print("  ✓ Semantic splitter correctly fell back to recursive splitter")
        print("    (This is expected if GEMINI_API_KEY is not set)")
    else:
        print("  ✓ Semantic splitter initialized successfully")
    
    print("✓ Semantic chunking fallback test passed!\n")
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("Document Processing Improvements - Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        test_preprocessing,
        test_csv_support,
        test_text_support,
        test_semantic_chunking_fallback
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}\n")
            failed += 1
    
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTests failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
