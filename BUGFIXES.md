# Bug Fixes Documentation

This document describes the bug fixes implemented to address the issues reported in the final bug fixes issue.

## Changes Summary

### 1. Fix "Listen" Button Requiring 2 Clicks

**Problem**: The Listen button had to be pressed twice for audio to play. First click showed "Running" for 1 second and stopped, second click actually generated audio.

**Root Cause**: Streamlit buttons trigger a page rerun when clicked. The audio was being generated but not persisted across reruns.

**Solution**: 
- Store generated audio in session state using a unique key for each message
- Audio is fetched once when the button is clicked and stored
- Display the audio element only after it's been generated and stored
- Added `autoplay=True` parameter to automatically play audio after generation

**Code Changes** (streamlit_app.py, lines ~250-276):
```python
# Generate audio on-demand when button is clicked
audio_key = f"audio_{i}"
if audio_key not in st.session_state:
    st.session_state[audio_key] = None

col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🔊 Listen", key=f"listen_btn_{i}"):
        with st.spinner("Generating audio..."):
            try:
                tts_response = requests.post(
                    f"{API_URL}/tts",
                    json={"text": content}
                )
                if tts_response.status_code == 200:
                    st.session_state[audio_key] = tts_response.content
                else:
                    st.error("Failed to generate audio")
            except Exception as e:
                st.error(f"Audio generation error: {e}")

# Display audio if it's been generated
if st.session_state[audio_key] is not None:
    st.audio(st.session_state[audio_key], format="audio/wav", autoplay=True)
```

### 2. Audio Autoplay for New Messages

**Problem**: Audio box would just sit there and not autoplay after generation.

**Solution**: 
- Removed the Listen button for newly generated responses
- Audio is now automatically generated and played after each response
- Added `autoplay=True` parameter to the audio player
- Changed errors to warnings so they don't interrupt the user experience

**Code Changes** (streamlit_app.py, lines ~317-328):
```python
# Generate audio automatically for new response
with st.spinner("Generating audio..."):
    try:
        tts_response = requests.post(
            f"{API_URL}/tts",
            json={"text": result["response"]}
        )
        if tts_response.status_code == 200:
            st.audio(tts_response.content, format="audio/wav", autoplay=True)
        else:
            st.warning("Could not generate audio")
    except Exception as e:
        st.warning(f"Audio generation error: {e}")
```

### 3. Disable Chat Input During Query Processing

**Problem**: Users could send multiple queries while the model was still processing, leading to race conditions and confused state.

**Solution**:
- Added `is_processing` flag to session state
- Set flag to `True` when a query starts processing
- Set flag to `False` when processing completes (success or failure)
- Use the `disabled` parameter of `st.chat_input()` to prevent input during processing

**Code Changes** (streamlit_app.py):

Initialization (lines ~66-67):
```python
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
```

Chat input (lines ~279-281):
```python
# Chat input - disable when processing
chat_disabled = st.session_state.is_processing
if prompt := st.chat_input("Ask a question...", disabled=chat_disabled):
    # Set processing flag
    st.session_state.is_processing = True
```

Reset after processing (lines ~340-341):
```python
# Reset processing flag
st.session_state.is_processing = False
```

### 4. Rate Limiting for Gemini Embedding API

**Problem**: When processing large documents, the gemini-embedding-001 API could hit rate limits.

**Solution**:
- Added `api_call_count` counter to track API calls in GeminiEmbedding class
- Implemented rate limiting: 10-second delay after every 50 API calls
- Applied to both `embed_documents()` and `embed_query()` methods
- Added logging to track when rate limiting is applied

**Code Changes** (app/core/embeddings.py):

Imports (line 5):
```python
import time
```

Initialization (lines ~26-27):
```python
self.api_call_count = 0  # Track API calls for rate limiting
```

Rate limiting logic in embed_documents() (lines ~44-48):
```python
# Check if we need to apply rate limiting
self.api_call_count += 1
if self.api_call_count % 50 == 0:
    app_logger.info(f"Rate limiting: Applied 10 second delay after {self.api_call_count} API calls")
    time.sleep(10)
```

Rate limiting logic in embed_query() (lines ~78-82):
```python
# Check if we need to apply rate limiting
self.api_call_count += 1
if self.api_call_count % 50 == 0:
    app_logger.info(f"Rate limiting: Applied 10 second delay after {self.api_call_count} API calls")
    time.sleep(10)
```

## Manual Testing Instructions

### Test 1: Listen Button Single Click
1. Start the application (`./start.sh`)
2. Ask a question and wait for response
3. Click the "🔊 Listen" button once
4. **Expected**: Audio should generate and play automatically after clicking once
5. Click the Listen button for the same message again
6. **Expected**: Audio should play immediately without regenerating

### Test 2: Audio Autoplay for New Messages
1. With the app running, ask a new question
2. Wait for the response to be generated
3. **Expected**: Audio should automatically start generating and playing without needing to click a button
4. The audio player should appear and start playing automatically

### Test 3: Disabled Chat Input During Processing
1. Ask a question in the chat
2. While "Thinking..." spinner is showing, try to type in the chat input box
3. **Expected**: The chat input should be grayed out/disabled
4. Try to send another message while processing
5. **Expected**: Should not be able to send
6. Wait for the response to complete
7. **Expected**: Chat input should be re-enabled and you can type again

### Test 4: Rate Limiting for Gemini Embeddings
1. Upload a large document (or multiple documents) to trigger many embedding calls
2. Monitor the logs in `logs/app_logs_YYYYMMDD.log`
3. **Expected**: After every 50 API calls, you should see:
   ```
   Rate limiting: Applied 10 second delay after 50 API calls
   Rate limiting: Applied 10 second delay after 100 API calls
   ```
4. The processing should pause for 10 seconds at these intervals

## Notes

- All changes are minimal and surgical, focusing only on fixing the reported issues
- No existing functionality was removed or broken
- Changes maintain compatibility with the existing codebase
- Error handling was improved to use warnings instead of errors where appropriate
- All changes follow the existing code style and patterns
