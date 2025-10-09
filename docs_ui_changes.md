# Live API UI Changes - Visual Guide

## Main UI with Talk Buttons

```
┌─────────────────────────────────────────────────────────────────────┐
│  Sidebar                                                             │
│  ┌──────────────────┐                                               │
│  │ 🤖 DevKraft RAG  │                                               │
│  │                  │                                               │
│  │ Model Selection  │                                               │
│  │ [gemini ▼]       │                                               │
│  │                  │                                               │
│  │ 📄 Upload Doc    │                                               │
│  │ [Choose file]    │                                               │
│  │                  │                                               │
│  │ 💬 Recent Chats  │                                               │
│  │ [➕ New Chat]    │                                               │
│  └──────────────────┘                                               │
│                                                                      │
│  Main Content Area                                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  Welcome to Devkraft RAG  │ [🎤 Talk (English)] [🎤 Talk (Hindi)] │
│  │  Current Model: GEMINI     │                                 │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────┐    │  │
│  │  │ Chat Messages                                        │    │  │
│  │  │                                                       │    │  │
│  │  │ 👤 User: What is RAG?                                │    │  │
│  │  │                                                       │    │  │
│  │  │ 🤖 Assistant: RAG stands for Retrieval...           │    │  │
│  │  │    [🔊 Listen]                                       │    │  │
│  │  │                                                       │    │  │
│  │  └─────────────────────────────────────────────────────┘    │  │
│  │                                                               │  │
│  │  [💬 Ask a question...]                                      │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Live API Modal (When Talk button is clicked)

```
┌─────────────────────────────────────────────────────────────────────┐
│  ─────────────────────────────────────────────────────────────────  │
│  🎤 Live Voice Interaction (en-IN)                                  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ℹ️ Live API Voice Interaction                                 │  │
│  │                                                                │  │
│  │ This feature uses Gemini's Live API for real-time voice       │  │
│  │ conversation.                                                  │  │
│  │                                                                │  │
│  │ How to use:                                                    │  │
│  │ 1. Click "Start Session" to begin                             │  │
│  │ 2. Type your message or speak (audio input coming soon)       │  │
│  │ 3. Get real-time audio responses from the AI                  │  │
│  │                                                                │  │
│  │ Note: Currently supports text input with audio output.        │  │
│  │ Full audio input/output requires browser microphone           │  │
│  │ permissions.                                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [✅ Start Session]        [❌ Close]                               │
│                                                                      │
│  Type your message:                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Enter text to send via Live API...                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [📤 Send]                                                          │
│                                                                      │
│  ─────────────────────────────────────────────────────────────────  │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Features Added:

1. **Talk Buttons in Top Bar**
   - Two buttons added next to the main title
   - 🎤 Talk (English) - for English (India) voice interaction
   - 🎤 Talk (Hindi) - for Hindi (India) voice interaction

2. **Live API Modal**
   - Opens when any Talk button is clicked
   - Shows instructions for using the Live API
   - Provides Start Session and Close buttons
   - Text input field for sending messages
   - Send button to submit text and receive audio response

3. **Language Selection**
   - English (India) - en-IN
   - Hindi (India) - hi-IN
   - Language is automatically set based on which Talk button is clicked

4. **Existing Features Maintained**
   - Regular chat input still works
   - Listen buttons still available on chat responses
   - All other features remain unchanged

## Technical Implementation:

- Uses Gemini Live API (gemini-2.5-flash-native-audio-preview-09-2025)
- Native audio output with automatic language selection
- Proactive audio support enabled
- Session management for maintaining conversation context
- RESTful API endpoints for Live API integration
