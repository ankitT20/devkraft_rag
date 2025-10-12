# Live Voice RAG - Frontend

This directory contains the frontend for the Live Voice RAG feature.

## Files

- **`voice.html`** - Main HTML page for the voice interface
- **`voice.css`** - Styling for the voice interface
- **`voice.js`** - JavaScript client using `@google/genai` SDK
- **`package.json`** - NPM package configuration (optional local installation)

## JavaScript SDK

The voice interface uses the `@google/genai` JavaScript SDK to connect directly to Gemini Live API.

### Default: CDN (No Installation Required)

By default, the SDK is loaded from the ESM CDN:
```javascript
import { GoogleGenAI, Modality } from 'https://esm.run/@google/genai';

// Initialize with v1alpha for ephemeral token support (required)
const ai = new GoogleGenAI({ 
    apiKey: ephemeralToken,
    httpOptions: { apiVersion: 'v1alpha' }
});
```

This requires no setup and works in most browsers. **Important**: The `v1alpha` API version is required for ephemeral token authentication.

### Alternative: Local Installation

If the CDN is blocked by ad blockers or corporate firewalls, you can install the SDK locally:

```bash
cd static
npm install
```

Then modify the import in `voice.js`:
```javascript
import { GoogleGenAI, Modality } from '/static/node_modules/@google/genai/dist/index.mjs';
```

**Note:** The `node_modules` directory is in `.gitignore` and won't be committed to the repository.

## How It Works

1. **Ephemeral Token Authentication**: Backend generates short-lived tokens via `/api/generate-token`
2. **SDK Connection**: Frontend uses `GoogleGenAI` client with the ephemeral token
3. **Live Session**: Establishes bidirectional audio streaming with Gemini Live API
4. **Function Calling**: Model can call `search_knowledge_base` to access RAG data
5. **Real-time Audio**: Native audio input (16kHz) and output (24kHz) without text conversion

## Security

- ✅ No API keys in frontend code
- ✅ Ephemeral tokens with 30-minute expiry
- ✅ Single-use tokens for each session
- ✅ Client-to-server architecture (no backend audio proxy)

## Browser Requirements

- Modern browser with Web Audio API support
- Microphone access permissions
- WebSocket support
- ES6 modules support
