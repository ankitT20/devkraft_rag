# Data Ingestion Improvements

This document describes the improvements made to the data ingestion pipeline.

## Overview

The document ingestion system has been enhanced with:
1. **Linting and code quality tools**
2. **Text preprocessing and cleaning**
3. **Support for CSV files**
4. **Support for website URLs**
5. **Semantic chunking option**

## 1. Linting and Code Quality

### Tools Added
- **Black**: Code formatter (line length: 100)
- **isort**: Import sorting
- **flake8**: Linting and code style checker
- **pytest**: Testing framework
- **playwright**: Browser automation for UI testing

### Configuration Files
- `.flake8`: Flake8 configuration
- `pyproject.toml`: Black and isort configuration

### Usage
```bash
# Format code
black app/ streamlit_app.py

# Sort imports
isort app/ streamlit_app.py

# Lint code
flake8 app/ streamlit_app.py

# Run tests
pytest tests/ -v
```

## 2. Text Preprocessing

### Features
The `preprocess_text()` method cleans documents by:
- Removing page numbers (e.g., "Page 5", "- 10 -")
- Removing excessive whitespace
- Standardizing line breaks
- Trimming leading/trailing whitespace

### Example
```python
from app.services.document_processor import DocumentProcessor

processor = DocumentProcessor()
clean_text = processor.preprocess_text(raw_text)
```

## 3. CSV Support

### Loading CSV Files
CSV files are now supported as a document type. Each row is converted to text and then chunked.

### Example
```python
# Via API
curl -X POST http://localhost:8000/upload \
  -F "file=@data.csv"

# Via Python
from app.services.document_processor import DocumentProcessor
processor = DocumentProcessor()
chunks, metadata = processor.load_document('path/to/file.csv')
```

### CSV Format
Any CSV file with headers is supported. The loader converts each row to a readable format:
```
column1: value1
column2: value2
...
```

## 4. Website URL Support

### Loading Websites
You can now ingest content directly from websites using the WebBaseLoader.

### API Endpoint
```bash
# New endpoint: /ingest-url
curl -X POST http://localhost:8000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### Streamlit UI
The UI now has two tabs:
1. **Upload File**: For local files (PDF, TXT, DOCX, MD, CSV)
2. **Ingest URL**: For website URLs

### Example
```python
from app.services.document_processor import DocumentProcessor
processor = DocumentProcessor()
chunks, metadata = processor.load_document('https://example.com')
```

## 5. Semantic Chunking

### Overview
Semantic chunking uses embeddings to create more meaningful chunks based on semantic similarity, rather than just character count.

### Usage
```python
from app.services.document_processor import DocumentProcessor

# Enable semantic chunking
processor = DocumentProcessor(use_semantic_chunking=True)
chunks, metadata = processor.load_document('path/to/file.txt')
```

### Implementation Details
- Uses `SemanticChunker` from `langchain_experimental`
- Requires embedding model (uses Gemini embeddings by default)
- Falls back to `RecursiveCharacterTextSplitter` if initialization fails

### Trade-offs
- **Pros**: Better semantic coherence, context-aware splits
- **Cons**: Slower processing, requires embedding model, higher API costs

## Dependencies Added

```
langchain-experimental>=0.3.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
unstructured[md]>=0.10.0
markdown>=3.5.0
flake8>=7.0.0
black>=24.0.0
isort>=5.13.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
playwright>=1.40.0
```

## Testing

### Unit Tests
```bash
pytest tests/test_document_processor.py -v
```

### Integration Tests
```bash
pytest tests/test_integration.py -v
```

### All Tests
```bash
pytest tests/ -v
```

## Migration Guide

### Existing Code
No changes needed! The improvements are backward compatible:
- Default chunking still uses `RecursiveCharacterTextSplitter`
- Existing document types (PDF, TXT, DOCX, MD) work as before
- API endpoints remain unchanged

### New Features
To use new features:

1. **CSV Files**: Just upload them like any other document
2. **Website URLs**: Use the new `/ingest-url` endpoint or UI tab
3. **Semantic Chunking**: Pass `use_semantic_chunking=True` to DocumentProcessor
4. **Preprocessing**: Automatically applied to all documents

## Examples

### CSV Ingestion
```python
from app.services.ingestion import IngestionService

service = IngestionService()
success, message = service.ingest_document('products.csv')
print(f"Success: {success}, Message: {message}")
```

### URL Ingestion
```python
from app.services.ingestion import IngestionService

service = IngestionService()
success, message = service.ingest_document('https://example.com/docs')
print(f"Success: {success}, Message: {message}")
```

### Preprocessing Check
```python
from app.services.document_processor import DocumentProcessor

processor = DocumentProcessor()
raw = "Page 1\n\nContent here\n\n\n\nMore content"
clean = processor.preprocess_text(raw)
print(clean)  # "Content here\n\nMore content"
```

## Performance Considerations

1. **Semantic Chunking**: Slower due to embedding generation
2. **Website Loading**: Speed depends on website response time
3. **CSV Files**: Fast, similar to text files
4. **Preprocessing**: Minimal overhead, regex-based

## Troubleshooting

### Issue: "Module 'unstructured' not found"
**Solution**: Install with `pip install "unstructured[md]>=0.10.0"`

### Issue: Website loading fails
**Solution**: Check internet connection, verify URL is accessible, check for rate limiting

### Issue: CSV not parsing correctly
**Solution**: Ensure CSV has headers, check encoding (UTF-8 recommended)

### Issue: Semantic chunking fails
**Solution**: Check API keys (GEMINI_API_KEY), verify embeddings model is accessible

## Future Improvements

Potential enhancements:
- Add more document types (JSON, XML, HTML files)
- Implement custom chunking strategies
- Add document validation
- Support for compressed files (ZIP, TAR)
- Parallel processing for bulk ingestion
- Progress tracking for large documents
