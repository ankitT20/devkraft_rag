# Data Ingestion Improvements

This document summarizes the improvements made to the data ingestion system using LangChain.

## Overview

The data ingestion system has been significantly enhanced with:
- Advanced text preprocessing
- Semantic chunking capabilities
- Support for CSV files and websites
- Improved document handling using LangChain loaders

## Changes Made

### 1. Dependencies Added

**requirements.txt:**
- `langchain-text-splitters>=0.3.0` - Enhanced text splitting
- `langchain-experimental>=0.3.0` - Semantic chunking
- `beautifulsoup4>=4.12.0` - Web scraping
- `lxml>=5.0.0` - HTML/XML parsing
- `unstructured>=0.10.0` - Document processing

### 2. Document Processor Enhancements

**File: `app/services/document_processor.py`**

#### Text Preprocessing
New method `_preprocess_text()` that:
- Removes excessive whitespace
- Removes common headers/footers patterns
- Removes page numbers
- Standardizes formatting

#### CSV Support
- Added `CSVLoader` from LangChain
- Properly handles CSV data with column names
- Creates appropriate metadata for CSV chunks

#### Website Support
New method `load_website()` that:
- Uses LangChain `WebBaseLoader`
- Extracts clean text from web pages
- Applies preprocessing and chunking
- Includes source URL in metadata

#### Semantic Chunking
- Implemented `SemanticChunker` with Gemini embeddings
- Intelligently splits text at semantic boundaries
- Falls back to `RecursiveCharacterTextSplitter` if unavailable
- Preserves context better than fixed-size chunking

### 3. Ingestion Service Updates

**File: `app/services/ingestion.py`**

#### Website Ingestion
New method `ingest_website()` that:
- Loads content from URLs
- Generates embeddings
- Stores in both cloud and docker vector databases
- Tracks success/failure status

#### Enhanced Document Processing
- Updated to support CSV files in `ingest_all_documents()`
- Improved error handling and logging

### 4. API Endpoints

**File: `app/main.py`**

#### New Endpoint: `/ingest-website`
```python
POST /ingest-website
Body: {"url": "https://example.com"}
Response: {
  "success": bool,
  "message": str,
  "filename": str
}
```

### 5. UI Updates

**File: `streamlit_app.py`**

- Updated file uploader to accept CSV files
- Changed `type=["txt", "pdf", "docx", "md"]` to `type=["txt", "pdf", "docx", "md", "csv"]`

### 6. Documentation

**File: `README.md`**

Updated sections:
- Document Processing - Added preprocessing details
- Chunking Strategy - Documented semantic chunking
- Supported Formats - Added CSV and websites
- API Endpoints - Added `/ingest-website`

### 7. Test Suite

**File: `test_document_improvements.py`**

Comprehensive tests for:
- Text preprocessing functionality
- CSV file loading and chunking
- Text file support
- Semantic chunking with fallback

All tests are passing successfully.

## How to Use

### Uploading CSV Files

1. Via UI:
   - Select CSV file in file uploader
   - Click "Upload" button
   - File is processed and stored in vector databases

2. Via API:
   ```bash
   curl -X POST http://localhost:8000/upload \
     -F "file=@data.csv"
   ```

### Ingesting Websites

Via API:
```bash
curl -X POST http://localhost:8000/ingest-website \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Semantic Chunking

Semantic chunking is enabled by default. It uses Gemini embeddings to find natural breakpoints in text, preserving context better than fixed-size chunking.

To disable semantic chunking:
```python
processor = DocumentProcessor(use_semantic_chunking=False)
```

## Benefits

1. **Better Chunking Quality**: Semantic chunking preserves context
2. **Cleaner Text**: Preprocessing removes noise and formatting issues
3. **More Data Sources**: CSV files and websites now supported
4. **Improved Accuracy**: Better chunking leads to better retrieval
5. **Flexible**: Fallback mechanisms ensure reliability

## Testing

Run the test suite:
```bash
python3 test_document_improvements.py
```

All tests should pass, demonstrating:
- ✅ Text preprocessing works correctly
- ✅ CSV files can be loaded and chunked
- ✅ Semantic chunking initializes properly
- ✅ Fallback mechanisms work as expected

## Notes

- Semantic chunking requires a valid Gemini API key
- If the API key is not available, the system automatically falls back to RecursiveCharacterTextSplitter
- Website ingestion requires internet connectivity
- All new features use LangChain for consistency and maintainability
