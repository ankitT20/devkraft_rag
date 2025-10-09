# Troubleshooting Guide - Live API Audio Client

## Common Issues and Solutions

### 1. "Could not find platform independent libraries" (Windows)

**Problem:**
```
Could not find platform independent libraries
```

**Cause:** 
This is a Windows-specific Python virtual environment issue. The virtual environment may be corrupted or improperly configured.

**Solution:**

#### Option A: Recreate Virtual Environment (Recommended)
```powershell
# 1. Deactivate current environment
deactivate

# 2. Delete old virtual environment
Remove-Item -Recurse -Force .venv

# 3. Create new virtual environment
python -m venv .venv

# 4. Activate new environment
.venv\Scripts\activate

# 5. Upgrade pip
python -m pip install --upgrade pip

# 6. Install dependencies
pip install -r requirements.txt

# 7. Verify installation
python -c "import pyaudio; import google.genai; print('✓ All dependencies installed')"

# 8. Run the client
python live_audio_client.py --language en-IN
```

#### Option B: Use System Python (No Virtual Environment)
```powershell
# 1. Deactivate virtual environment
deactivate

# 2. Install dependencies globally
pip install -r requirements.txt

# 3. Run the client
python live_audio_client.py --language en-IN
```

#### Option C: Use Conda (If you have Anaconda/Miniconda)
```powershell
# 1. Create conda environment
conda create -n devkraft python=3.11

# 2. Activate environment
conda activate devkraft

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the client
python live_audio_client.py --language en-IN
```

---

### 2. PyAudio Installation Failed (Windows)

**Problem:**
```
ERROR: Could not build wheels for pyaudio
```

**Cause:** 
PyAudio requires compiled binaries which may not be available for your Python version.

**Solution:**

#### Option A: Install Pre-compiled Wheel
```powershell
# Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# Example for Python 3.11, 64-bit:
pip install PyAudio-0.2.14-cp311-cp311-win_amd64.whl
```

#### Option B: Install Via Conda
```powershell
conda install pyaudio
```

#### Option C: Install Build Tools
```powershell
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Then:
pip install pyaudio
```

---

### 3. No Microphone Detected

**Problem:**
```
OSError: [Errno -9996] Invalid input device
```

**Solution:**
```python
# List available audio devices
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"

# Select specific device by editing live_audio_client.py:
# Change line in listen_audio method:
mic_info = pya.get_device_info_by_index(YOUR_DEVICE_ID)
```

---

### 4. GEMINI_API_KEY Not Set

**Problem:**
```
ValueError: GEMINI_API_KEY environment variable not set
```

**Solution:**

#### Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
python live_audio_client.py --language en-IN
```

#### Windows CMD:
```cmd
set GEMINI_API_KEY=your_api_key_here
python live_audio_client.py --language en-IN
```

#### Linux/Mac:
```bash
export GEMINI_API_KEY="your_api_key_here"
python live_audio_client.py --language en-IN
```

#### Permanent (Add to .env file):
```bash
# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env

# The script will automatically load it
python live_audio_client.py --language en-IN
```

---

### 5. Import Error for google.genai

**Problem:**
```
ImportError: No module named 'google.genai'
```

**Solution:**
```powershell
pip install --upgrade google-genai
```

---

### 6. Audio Not Playing

**Problem:**
No sound coming from speakers

**Solution:**

#### Check Default Output Device:
```python
python -c "import pyaudio; p=pyaudio.PyAudio(); print(p.get_default_output_device_info())"
```

#### Check Volume:
- Ensure system volume is not muted
- Check speaker connections
- Test with other audio applications

#### Specify Output Device:
Edit `live_audio_client.py` and modify the `play_audio` method to specify device.

---

### 7. High Latency or Choppy Audio

**Problem:**
Audio has delays or stutters

**Solution:**

#### Adjust Chunk Size:
```python
# In live_audio_client.py, change:
CHUNK_SIZE = 512  # Smaller = lower latency but more CPU
# or
CHUNK_SIZE = 2048  # Larger = higher latency but more stable
```

#### Close Other Applications:
- Close browser tabs
- Close other audio applications
- Free up system resources

---

### 8. Rate Limit Exceeded

**Problem:**
```
429: Too Many Requests
```

**Solution:**

The model has strict rate limits:
- 1 concurrent session
- 25,000 tokens per minute
- 5 requests per day

Wait before trying again or upgrade your API quota.

---

### 9. Voice Activity Detection Not Working

**Problem:**
AI doesn't respond when you speak

**Solution:**

#### Check Microphone:
```powershell
# Test microphone
python -c "import pyaudio; p=pyaudio.PyAudio(); s=p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True); print('Speak now...'); d=s.read(16000); print(f'Recorded {len(d)} bytes'); s.close()"
```

#### Speak Clearly:
- Speak louder
- Move closer to microphone
- Reduce background noise
- Wait 1-2 seconds between sentences

#### VAD Settings:
Voice Activity Detection is automatic. If it's too sensitive or not sensitive enough, this is controlled by the Gemini Live API and cannot be adjusted client-side.

---

### 10. Connection Errors

**Problem:**
```
WebSocketException: Connection failed
```

**Solution:**

#### Check Internet Connection:
```powershell
ping ai.google.dev
```

#### Check Firewall:
- Ensure Python is allowed through firewall
- Check corporate proxy settings
- Try on different network

#### Check API Key:
```powershell
# Verify API key is valid
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1beta/models
```

---

## System Requirements

### Minimum Requirements:
- Python 3.8 or higher
- Windows 10/11, macOS 10.14+, or Linux
- Microphone and speakers
- Internet connection
- Valid GEMINI_API_KEY

### Recommended:
- Python 3.10 or 3.11
- 4GB RAM
- Good quality microphone
- Headphones (to prevent echo)
- Stable internet (10+ Mbps)

---

## Testing Your Setup

### 1. Test Python Installation:
```powershell
python --version
# Should show Python 3.8 or higher
```

### 2. Test Dependencies:
```powershell
python -c "import pyaudio; import google.genai; print('✓ All imports successful')"
```

### 3. Test Audio Devices:
```powershell
python -c "import pyaudio; p=pyaudio.PyAudio(); print(f'Audio devices: {p.get_device_count()}')"
```

### 4. Test API Key:
```powershell
python -c "import os; print('✓ API Key set' if os.getenv('GEMINI_API_KEY') else '✗ API Key not set')"
```

### 5. Test Full Setup:
```powershell
python live_audio_client.py --language en-IN
# Should show "🎤 Microphone active" and "🔊 Speaker active"
```

---

## Getting Help

If you still have issues:

1. **Check the error message carefully** - it usually tells you what's wrong
2. **Search GitHub Issues** - someone may have had the same problem
3. **Create a new issue** with:
   - Error message (full traceback)
   - Python version: `python --version`
   - OS version
   - Steps to reproduce
   - What you've already tried

---

## Quick Reference

### Start the Client:
```powershell
# English
python live_audio_client.py --language en-IN

# Hindi
python live_audio_client.py --language hi-IN
```

### Stop the Client:
- Press `Ctrl+C`

### Check Status:
- ✓ = Working correctly
- ✗ = Problem detected
- Look for error messages in red

---

## Alternative: Use Text-Based Interaction

If audio isn't working, you can still use the web UI:

```powershell
# Start the web interface
./start.sh
# or
streamlit run streamlit_app.py
```

Then use the text input in the Live API modal for interaction without audio.
