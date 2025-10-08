# Streaming Feature - User Guide

## What's New?

The DevKraft RAG application now features **real-time streaming responses**! This means you'll see the AI's response appear word-by-word as it's being generated, instead of waiting with a spinner.

## User Experience Comparison

### ❌ Before (No Streaming)

**What you saw:**
1. Type your question
2. Click Send
3. See "Thinking..." spinner for 5-20 seconds
4. ⏰ **Wait... wait... wait...**
5. Finally, the complete response appears all at once

**Problems:**
- No feedback during generation
- Uncertain wait time
- Frustrating for long responses
- Looks like the app is frozen

### ✅ After (With Streaming)

**What you see now:**
1. Type your question
2. Click Send
3. Response starts appearing immediately!
4. ✨ **Watch the text appear character-by-character**
5. Cursor indicator (▌) shows generation is in progress
6. Metadata (sources, thinking) appears when complete

**Benefits:**
- Immediate visual feedback
- Know the AI is working
- Engaging experience
- Read as it generates

## Visual Indicators

### During Streaming
```
Here is the complete response that appears▌
```
The blinking cursor (▌) shows that more text is coming.

### After Streaming
```
Here is the complete response that appears gradually, word by word!

📚 Show Sources (expandable)
🧠 Show Thinking (expandable, Qwen3 only)
```

## How to Use

### Basic Query
1. Open the Streamlit UI (http://localhost:8501)
2. Type your question in the chat input
3. Press Enter or click Send
4. **Watch the magic!** Response streams in real-time

### Switching Models
Both models now support streaming:
- **Gemini (Cloud)**: Uses Google's streaming API
- **Qwen3 (Local)**: Streams from LM Studio or HuggingFace

Simply select your preferred model in the sidebar - streaming works automatically!

## Features That Still Work

All existing features are preserved:

### ✅ Chat History
- Conversations are saved
- Load previous chats from sidebar
- Full context maintained

### ✅ Sources
- Relevant documents shown after response
- Click to expand and view details
- Original text available

### ✅ Thinking (Qwen3)
- Model's reasoning process displayed
- Expandable section below response
- Helps understand decision-making

### ✅ Document Upload
- Add new documents to knowledge base
- Processed and indexed automatically
- Available for all future queries

### ✅ Text-to-Speech
- Listen button still available
- Converts response to audio
- Works with streaming responses

## Technical Details (For Curious Users)

### What's Happening Behind the Scenes?

1. **Your Query** → Sent to backend
2. **Vector Search** → Finds relevant documents
3. **AI Generation** → Starts creating response
4. **Streaming** → Each word/chunk sent immediately
5. **Display** → UI updates in real-time
6. **Metadata** → Sources and thinking added at end

### Performance Impact

- **Latency**: Minimal (response starts ~100ms faster)
- **Bandwidth**: Slightly higher (streaming overhead)
- **Experience**: Significantly better!

### Network Considerations

Streaming works best with:
- ✅ Stable internet connection
- ✅ Low latency to backend
- ✅ Modern browser (Chrome, Firefox, Edge)

May experience delays with:
- ⚠️ Slow network connections
- ⚠️ High latency (>500ms)
- ⚠️ Network interruptions

## Troubleshooting

### Response Not Streaming?

**Check these:**
1. Ensure backend is running (`http://localhost:8000/health`)
2. Check browser console for errors (F12)
3. Verify network connection is stable
4. Try refreshing the page (F5)

### Streaming Stops Midway?

**Possible causes:**
1. Network timeout - check connection
2. Backend error - check logs
3. Model API issue - try different model

### Text Appears Too Fast/Slow?

This depends on:
- Model generation speed
- Network latency
- Response length
- Server load

Unfortunately, speed cannot be adjusted by users - it's based on actual generation speed.

## FAQ

**Q: Can I disable streaming?**
A: Currently, streaming is enabled by default. The old `/query` endpoint still exists for non-streaming requests if needed for API integrations.

**Q: Does streaming use more resources?**
A: Minimal difference. The response is sent in small chunks instead of one large chunk, but total data transferred is the same.

**Q: What if streaming fails?**
A: The system will show an error message. You can retry the query, and it may fall back to non-streaming mode.

**Q: Does streaming work on mobile?**
A: Yes! The Streamlit UI is responsive and streaming works on mobile browsers.

**Q: Can I see partial sources while streaming?**
A: No, sources are displayed only after streaming completes to avoid confusion. The AI needs to finish generating before determining which sources were most relevant.

**Q: Does thinking stream for Qwen3?**
A: No, the thinking process is extracted and shown after the main response completes. This is because thinking tags need to be parsed from the complete response.

## Tips for Best Experience

1. **Use a stable connection** - WiFi or wired for best results
2. **Keep browser tab active** - Streaming may pause if tab is in background
3. **Clear browser cache** - If you experience issues after updates
4. **Use modern browser** - Chrome, Firefox, Edge for best compatibility

## Feedback

Love the new streaming feature? Have suggestions? 

Please provide feedback through:
- GitHub Issues: Report bugs or request features
- Pull Requests: Contribute improvements
- Discussions: Share your experience

---

**Enjoy the new streaming experience! 🚀✨**
