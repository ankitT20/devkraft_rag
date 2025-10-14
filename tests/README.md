# Tests

This directory contains the test suite for the DevKraft RAG application.

## Test Files

### `test_document_processor.py`
Unit tests for the document processor:
- Text preprocessing (page number removal, whitespace cleanup)
- CSV file loading
- Text file loading
- Chunking behavior

### `test_integration.py`
Integration tests for end-to-end document processing:
- CSV file integration with real files
- Markdown with preprocessing
- Long content handling and chunking

### `test_ui_playwright.py`
Placeholder for UI tests using Playwright (requires running application):
- Document upload functionality
- URL ingestion UI
- Chat interface

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Test File
```bash
pytest tests/test_document_processor.py -v
```

### With Coverage
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Specific Test
```bash
pytest tests/test_document_processor.py::TestDocumentProcessor::test_preprocess_text_removes_page_numbers -v
```

## Test Requirements

Dependencies are in `requirements.txt`:
- pytest>=8.0.0
- pytest-asyncio>=0.23.0
- playwright>=1.40.0 (for UI tests)

Install with:
```bash
pip install -r requirements.txt
```

## Test Results

Current status: **All tests passing ✅**

```
collected 8 items

test_document_processor.py::TestDocumentProcessor::test_preprocess_text_removes_page_numbers PASSED
test_document_processor.py::TestDocumentProcessor::test_preprocess_text_removes_excessive_whitespace PASSED
test_document_processor.py::TestDocumentProcessor::test_load_csv_document PASSED
test_document_processor.py::TestDocumentProcessor::test_load_text_document PASSED
test_document_processor.py::TestDocumentProcessor::test_chunk_text_with_recursive_splitter PASSED
test_integration.py::TestIntegrationDocumentProcessing::test_csv_integration PASSED
test_integration.py::TestIntegrationDocumentProcessing::test_markdown_with_preprocessing PASSED
test_integration.py::TestIntegrationDocumentProcessing::test_text_file_with_long_content PASSED

8 passed in 2.5s
```

## Writing New Tests

### Example Unit Test
```python
def test_new_feature(self):
    """Test a new feature."""
    processor = DocumentProcessor()
    result = processor.some_method()
    assert result is not None
```

### Example Integration Test
```python
def test_new_integration(self):
    """Integration test for new workflow."""
    # Setup
    processor = DocumentProcessor()
    
    # Execute
    chunks, metadata = processor.load_document(file_path)
    
    # Verify
    assert len(chunks) > 0
    assert len(metadata) == len(chunks)
```

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root:
```bash
cd /path/to/devkraft_rag
python -m pytest tests/ -v
```

### Missing Dependencies
Install all test dependencies:
```bash
pip install pytest pytest-asyncio playwright
```

### Playwright Tests
For Playwright tests, install browsers:
```bash
playwright install
```

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Add integration tests for complex workflows
4. Update this README if adding new test files
