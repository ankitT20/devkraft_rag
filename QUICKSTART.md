# DevKraft RAG - Quick Start Guide

Get up and running with DevKraft RAG in minutes!

## Prerequisites

- Python 3.8 or higher
- API Keys (set as environment variables):
  - `GEMINI_API_KEY` - Google Gemini API key
  - `QDRANT_API_KEY` - Qdrant Cloud API key
  - `HF_TOKEN` - HuggingFace API token

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ankitT20/devkraft_rag.git
cd devkraft_rag
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

**Linux/Mac:**
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export QDRANT_API_KEY="your_qdrant_api_key"
export HF_TOKEN="your_huggingface_token"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your_gemini_api_key
set QDRANT_API_KEY=your_qdrant_api_key
set HF_TOKEN=your_huggingface_token
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
$env:QDRANT_API_KEY="your_qdrant_api_key"
$env:HF_TOKEN="your_huggingface_token"
```

## Running the Application

### Method 1: Using startup scripts (Recommended)

**Terminal 1 - Start API Server:**
```bash
./start_api.sh
```

**Terminal 2 - Start UI:**
```bash
./start_ui.sh
```

### Method 2: Manual start

**Terminal 1 - Start API Server:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run streamlit_app.py
```

### Access the application

- **Streamlit UI:** http://localhost:8501
- **FastAPI Docs:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health

## First Steps

### 1. Upload a Document

1. Open the Streamlit UI at http://localhost:8501
2. Look for "📄 Upload Document" in the left sidebar
3. Click "Browse files" and select a document (TXT, PDF, DOCX, or MD)
4. Click the "➕ Upload" button
5. Wait for the document to be processed and ingested

### 2. Select Your Model

In the sidebar, you'll see "Model Selection":
- **Gemini Cloud** (Default): Fast, cloud-based processing
- **Qwen3 Local**: Local processing with HuggingFace fallback

### 3. Ask Questions

1. Type your question in the chat input at the bottom
2. Press Enter
3. The AI will search your documents and provide an answer with context

### 4. View Chat History

- Recent chats appear in the "💬 Recent Chats" section
- Click any chat to reload it
- Click "➕ New Chat" to start fresh

## Example Workflow

```
1. Upload "company_policy.pdf"
   ↓
2. Wait for "Successfully ingested to cloud"
   ↓
3. Ask: "What is the vacation policy?"
   ↓
4. Get AI response with relevant excerpts from your document
```

## API Usage

You can also interact with the API directly:

### Query Endpoint

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key features?",
    "model_type": "gemini"
  }'
```

### Upload Endpoint

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@path/to/document.pdf"
```

### Get Recent Chats

```bash
curl http://localhost:8000/chats?limit=10
```

## Troubleshooting

### Issue: "Connection refused" for Qdrant Docker

**Solution:** The application will automatically fall back to Qdrant Cloud. This is expected if you don't have Qdrant running locally.

### Issue: "LM Studio not available"

**Solution:** The application will automatically use HuggingFace API as fallback. This is expected if you don't have LM Studio running locally.

### Issue: API returns 500 error

**Solution:** Check that all environment variables are set correctly:
```bash
echo $GEMINI_API_KEY
echo $QDRANT_API_KEY
echo $HF_TOKEN
```

### Issue: Document upload fails

**Solution:** 
- Ensure the file format is supported (TXT, PDF, DOCX, MD)
- Check that the file is not corrupted
- Look at logs in `logs/errors_*.log` for details

## Understanding the Models

### Gemini Cloud (gemini-2.5-flash)
- **Best for:** Production use, fast responses
- **Embeddings:** 3072 dimensions
- **Storage:** Qdrant Cloud
- **Cost:** Requires Gemini API credits

### Qwen3 Local (qwen3-1.7b)
- **Best for:** Learning, local development
- **Embeddings:** 768 dimensions with HF fallback
- **Storage:** Qdrant Docker (with Cloud replication)
- **Special:** Shows thinking process in UI
- **Cost:** Free (using HF fallback)

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API documentation at http://localhost:8000/docs
- Check logs in `logs/` folder for detailed application behavior
- Add more documents to build your knowledge base

## Support

For issues, please check:
1. Application logs: `logs/app_logs_*.log`
2. Error logs: `logs/errors_*.log`
3. GitHub Issues: https://github.com/ankitT20/devkraft_rag/issues

Enjoy using DevKraft RAG! 🚀
