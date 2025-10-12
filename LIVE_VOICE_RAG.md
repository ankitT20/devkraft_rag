# Live Voice RAG - Documentation

## Overview

The Live Voice RAG feature enables real-time voice interaction with your document knowledge base using Gemini's native audio model. Users can have natural conversations with the AI assistant, which can search through uploaded documents to provide accurate answers.

## Features

- **Native Audio**: Uses Gemini 2.5 Flash Native Audio model for natural, realistic speech
- **Real-time Interaction**: Low-latency bidirectional audio streaming
- **RAG Integration**: Automatically searches vector database when needed
- **Function Calling**: Seamless integration with knowledge base search
- **Dynamic Thinking**: Model intelligently processes complex queries
- **Multi-language Support**: Automatically detects and responds in user's language
- **Secure Authentication**: Uses ephemeral tokens for client-side security
- **Voice**: Achird voice for consistent audio quality

## Architecture

### Client-to-Server Approach
The implementation uses a client-to-server architecture where:
1. Frontend connects directly to Gemini Live API via WebSocket
2. Backend generates ephemeral tokens for secure authentication
3. Backend provides function endpoints for RAG operations
4. No audio streaming through the backend (lower latency)

### Components

#### Backend (FastAPI)
- **`/api/generate-token`**: Generates ephemeral tokens (30 min expiry)
- **`/api/function-declarations`**: Returns available RAG functions
- **`/api/search-knowledge-base`**: Executes vector search on knowledge base
- **`/voice`**: Serves the voice interface HTML page

#### Frontend (Static HTML/CSS/JS)
- **`voice.html`**: Main voice interface page
- **`voice.css`**: Styling for the voice interface
- **`voice.js`**: JavaScript SDK client (@google/genai) with audio handling
- **`package.json`**: NPM package configuration for JavaScript SDK

#### Core Services
- **`app/core/live_api.py`**: LiveAPIService for token management
- **`app/config.py`**: Configuration for the native audio model

## Configuration

### Model Settings
```python
MODEL = "gemini-2.5-flash-native-audio-preview-09-2025"
VOICE = "Achird"
RESPONSE_MODALITY = "AUDIO"
```

### Features Enabled
- ✅ Dynamic Thinking (no budget limit)
- ✅ Function Calling with Automatic Response
- ✅ Audio Input & Output (16kHz input, 24kHz output)
- ❌ Affective Dialog (incompatible with function calling)
- ❌ Proactive Audio (incompatible with function calling)

## Setup

The voice interface uses the JavaScript SDK (`@google/genai`) loaded via ESM CDN from `https://esm.run/@google/genai`, so no npm install is required by default.

**Optional: Local SDK Installation**  
If you encounter issues with the CDN (e.g., ad blockers or corporate firewalls), you can install the SDK locally:
```bash
cd static
npm install
```
Then modify the import in `voice.js` to use the local version:
```javascript
import { GoogleGenAI, Modality } from '/static/node_modules/@google/genai/dist/index.mjs';
```

## Usage

### From Streamlit Interface
1. Open the main RAG application at `http://localhost:8501`
2. In the sidebar, click the **🎤 Start Live Voice Call** button
3. This will open the voice interface in a new tab

### Direct Access
Navigate directly to `http://localhost:8000/voice`

### Using the Voice Interface

1. **Connect**: Click the "🔌 Connect" button to establish connection
   - System generates an ephemeral token (no API key exposure)
   - Connection established via JavaScript SDK (@google/genai)
   - Model initialized with RAG function declarations

2. **Start Talking**: Click the "🎤 Start Talking" button
   - Microphone access requested
   - Audio streaming begins (16-bit PCM, 16kHz)
   - Voice visualization displays audio waveform

3. **Conversation**:
   - Speak naturally to the assistant
   - AI automatically searches knowledge base when needed
   - Responses are played back in real-time (24kHz)
   - Conversation transcript displayed on screen

4. **Disconnect**: Click the "⏹️ Disconnect" button to end session

## Function Calling

The system defines one RAG function that the model can call:

```javascript
{
  "name": "search_knowledge_base",
  "description": "Search the knowledge base for relevant information",
  "parameters": {
    "query": "Search query string",
    "top_k": "Number of results (default: 3)"
  }
}
```

### Workflow
1. User asks a question via voice
2. Model determines if knowledge base search is needed
3. Model calls `search_knowledge_base` function with appropriate query
4. Backend searches Qdrant vector database
5. Results returned to model
6. Model synthesizes answer and responds via audio

## Technical Details

### Audio Processing
- **Input**: 16-bit PCM, 16kHz, mono channel
- **Output**: 16-bit PCM, 24kHz, mono channel
- **Processing**: Web Audio API for real-time handling
- **Codec**: Native audio (no intermediate text conversion)

### Security
- **Ephemeral Tokens**: Short-lived tokens (30 min expiry, 1 min to start session)
- **Single Use**: Each token can only start one session
- **No API Key Exposure**: API keys remain on server

### WebSocket Protocol
```
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent
```

## Limitations

1. **Response Modality**: Only AUDIO mode (cannot return text in same session)
2. **Feature Compatibility**: Cannot use affective dialog or proactive audio with function calling
3. **Browser Support**: Requires modern browser with Web Audio API support
4. **Network**: Requires stable internet connection for streaming

## API Endpoints

### Generate Token
```bash
GET /api/generate-token
```
Response:
```json
{
  "token": "auth_tokens/...",
  "expires_in": 1800,
  "new_session_expires_in": 60
}
```

### Get Function Declarations
```bash
GET /api/function-declarations
```
Response:
```json
{
  "functions": [
    {
      "name": "search_knowledge_base",
      "description": "...",
      "parameters": {...}
    }
  ]
}
```

### Search Knowledge Base
```bash
POST /api/search-knowledge-base
Content-Type: application/json

{
  "query": "What is RAG?",
  "top_k": 3
}
```
Response:
```json
{
  "results": [
    {
      "header": "...",
      "text": "...",
      "page": 1,
      "filename": "...",
      "score": 0.95
    }
  ],
  "count": 3
}
```

## Troubleshooting

### Connection Issues
- Verify API key is set correctly
- Check network connectivity
- Ensure port 8000 is accessible

### Audio Issues
- Grant microphone permissions in browser
- Check browser audio settings
- Verify speakers/headphones connected

### Function Call Failures
- Ensure Qdrant connection is active
- Verify documents are uploaded to knowledge base
- Check backend logs for errors

## Future Enhancements

Possible improvements:
- Session resumption for reconnection
- Video input support
- Multiple RAG functions (different search strategies)
- Audio recording download
- Conversation history export
- Custom voice selection
- Language preference setting

## References

- [Gemini Live API Documentation](https://ai.google.dev/gemini-api/docs/live)
- [Native Audio Models](https://ai.google.dev/gemini-api/docs/models/gemini)
- [Function Calling Guide](https://ai.google.dev/gemini-api/docs/function-calling)
- [Ephemeral Tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens)
