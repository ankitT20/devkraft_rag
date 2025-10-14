# Live API Transcript Display - Implementation

## Problem Statement

Gemini Live API has a fundamental limitation: **only ONE response modality can be set** per session - either `TEXT` or `AUDIO`, but not both simultaneously. This means when using the native audio model for voice responses, we cannot get text transcripts from the model's audio responses.

**Official Documentation Reference:**
> "Note: You can only set one modality in the response_modalities field. This means that you can configure the model to respond with either text or audio, but not both in the same session."

## Solution: Hybrid Transcript Display

Since we cannot compromise the Live API audio quality (as per requirements), we implemented a **hybrid approach** that shows what's possible:

### What We CAN Show (Implemented)

1. **User's Speech → Text** ✅
   - Uses Web Speech API (browser's built-in speech recognition)
   - Real-time transcription with interim results
   - Shown with blue background in transcript
   - Partial results shown in italics with dashed border

2. **Assistant Audio Indicator** ✅
   - Shows "[Speaking...]" when model responds with audio
   - Marked with 🔊 icon
   - Shown with green background in transcript

3. **System Messages** ✅
   - Connection status
   - Function calls (RAG searches)
   - Search results
   - Errors and warnings

4. **Function Call Details** ✅
   - "🔍 Searching knowledge base for: [query]"
   - "✓ Found N relevant sources"

### What We CANNOT Show (API Limitation)

1. **Model's Speech → Text** ❌
   - Not possible because model is in AUDIO mode
   - Would require TEXT mode, which loses audio quality
   - No workaround exists in Gemini API
   - This is a fundamental limitation of the Live API architecture

## Technical Implementation

### Web Speech API Integration

```javascript
// Initialize speech recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'en-US';

recognition.onresult = (event) => {
    // Show interim results (partial transcription)
    // Show final results (confirmed transcription)
};
```

### Browser Compatibility

- ✅ Chrome/Edge: Full support
- ✅ Safari: Full support (webkit prefix)
- ❌ Firefox: Limited support
- ⚠️ Note: Requires HTTPS or localhost

### Audio Response Indication

```javascript
// When receiving audio from model
if (part.inlineData.mimeType.startsWith('audio/')) {
    addTranscriptMessage('assistant', 'Assistant: [Speaking...]');
    playAudioChunk(part.inlineData.data);
}
```

## User Experience

The transcript panel now shows:

```
[Blue box] You: What is RAG?
[Yellow box] 🔍 Searching knowledge base for: "RAG"
[Yellow box] ✓ Found 3 relevant sources
[Green box] 🔊 Assistant: [Speaking...]
```

Users will:
- See their own speech transcribed in real-time
- See when the model is searching the knowledge base
- See when the model is responding with audio
- Hear the actual audio response (preserved quality)

## Why This is the Best Solution

1. **Preserves Audio Quality**: Native audio model provides best speech synthesis
2. **Shows User Intent**: User can see what they said
3. **Shows System Actions**: Function calls and searches are visible
4. **No Compromises**: Keeps the Live API audio experience intact
5. **Clear Communication**: UI clearly explains the limitation

## Alternative Approaches Considered

### ❌ Option 1: Use TEXT Mode
- **Problem**: Loses native audio, would need separate TTS
- **Result**: Worse audio quality, higher latency

### ❌ Option 2: Use Two Sessions (TEXT + AUDIO)
- **Problem**: Can't synchronize, double cost, complex state management
- **Result**: Not practical, poor UX

### ❌ Option 3: Server-Side STT on Model Output
- **Problem**: Model outputs audio directly, would need to:
  1. Stream audio to server
  2. Run STT service (Google Cloud STT, Whisper, etc.)
  3. Add latency and cost
- **Result**: Complex, expensive, defeats purpose of Live API

### ✅ Option 4: Web Speech API + Audio Indicators (Current)
- **Benefits**: 
  - Simple implementation
  - No additional cost
  - Real-time user transcription
  - Preserves audio quality
  - Clear about limitations

## Future Possibilities

If Gemini API adds support for dual modalities:
```javascript
// Future API (not currently supported)
responseModalities: [Modality.TEXT, Modality.AUDIO]
```

Then we could:
1. Get text transcripts from the model
2. Still play audio responses
3. Show both in sync

**Current Status**: Not available in Gemini Live API

## Configuration

No configuration needed. The system automatically:
1. Detects if Web Speech API is available
2. Falls back gracefully if not supported
3. Shows appropriate messages

## Troubleshooting

### Speech Recognition Not Working

1. **Check Browser Support**
   - Use Chrome, Edge, or Safari
   - Firefox has limited support

2. **Check HTTPS**
   - Requires HTTPS or localhost
   - Won't work on HTTP in production

3. **Check Microphone Permissions**
   - Browser must have mic access
   - Check browser settings

4. **Check Language**
   - Default is 'en-US'
   - Can be changed in code if needed

### No User Transcript Appearing

- Check browser console for errors
- Verify mic is working
- Try speaking louder/clearer
- Check if interim results are enabled

## Conclusion

This implementation provides the best possible transcript experience given the API constraints. It shows:
- ✅ What the user says (Web Speech API)
- ✅ What actions the system takes (function calls)
- ✅ When the model responds (audio indicator)
- ❌ What the model says in text (not possible with current API)

The limitation is clearly communicated to users in the UI, and the audio experience remains pristine.
