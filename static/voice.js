/**
 * Live Voice RAG - JavaScript client for Gemini Live API with native audio
 * Uses JavaScript SDK (@google/genai) with ephemeral tokens for secure authentication
 * 
 * IMPORTANT: Ephemeral tokens require v1alpha API version. Initialize client with:
 *   new GoogleGenAI({ apiKey: token, httpOptions: { apiVersion: 'v1alpha' } })
 * 
 * VOICE ACTIVITY DETECTION (VAD):
 *   - Automatic VAD is enabled by default (Gemini handles interruption detection)
 *   - Client-side VAD threshold (VAD_THRESHOLD) detects user speech to stop local playback
 *   - This prevents audio overlap when user interrupts the model
 *   - Server-side VAD handles the model's response to interruptions
 * 
 * Note: The SDK is loaded from esm.run CDN. If you have issues with CDN being blocked,
 * you can install the SDK locally:
 *   cd static && npm install
 * Then change the import to: import { GoogleGenAI, Modality } from '/static/node_modules/@google/genai/dist/index.mjs';
 */

import { GoogleGenAI, Modality } from 'https://esm.run/@google/genai';

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const MODEL = 'gemini-2.5-flash-native-audio-preview-09-2025';

// Debug flag
const DEBUG_AUDIO = true;

// Audio Configuration
const SEND_SAMPLE_RATE = 16000;
const RECEIVE_SAMPLE_RATE = 24000;

// Voice Activity Detection (VAD) threshold for client-side interruption
// Adjust this value if needed (higher = less sensitive, lower = more sensitive)
const VAD_THRESHOLD = 0.01;

// State
let liveSession = null;
let ephemeralToken = null;
let audioContext = null;
let audioStream = null;
let isConnected = false;
let isRecording = false;
let audioQueueTime = 0;
let audioProcessor = null;
let responseQueue = [];

// UI Elements
const connectBtn = document.getElementById('connect-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const transcript = document.getElementById('transcript');
const visualizer = document.getElementById('visualizer');
const canvasContext = visualizer.getContext('2d');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    connectBtn.addEventListener('click', handleConnectToggle);
    
    // Initialize visualizer
    drawVisualizerIdle();
});

/**
 * Update connection status
 */
function updateStatus(status, message) {
    statusDot.className = `status-dot ${status}`;
    statusText.textContent = message;
}

/**
 * Add message to transcript
 */
function addTranscriptMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = content;
    transcript.appendChild(messageDiv);
    transcript.scrollTop = transcript.scrollHeight;
}

/**
 * Handle Connect/Disconnect toggle
 */
async function handleConnectToggle() {
    if (!isConnected) {
        await handleConnect();
    } else {
        handleDisconnect();
    }
}

/**
 * Handle Connect button
 */
async function handleConnect() {
    try {
        updateStatus('connecting', 'Connecting...');
        connectBtn.disabled = true;
        
        // Clear transcript
        transcript.innerHTML = '<p class="system-message">Connecting to Live API...</p>';
        
        // Initialize audio context first
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: SEND_SAMPLE_RATE
            });
        }
        
        // Get ephemeral token from backend
        const tokenResponse = await fetch(`${API_BASE_URL}/api/generate-token`);
        if (!tokenResponse.ok) {
            throw new Error('Failed to get ephemeral token');
        }
        
        const tokenData = await tokenResponse.json();
        ephemeralToken = tokenData.token;
        
        addTranscriptMessage('system', 'Token obtained, connecting with JavaScript SDK...');
        
        // Get function declarations
        const functionsResponse = await fetch(`${API_BASE_URL}/api/function-declarations`);
        const functionsData = await functionsResponse.json();
        
        // Connect to Gemini Live API using JavaScript SDK
        await connectToLiveAPI(functionsData.functions);
        
    } catch (error) {
        console.error('Connection error:', error);
        addTranscriptMessage('error', `Connection failed: ${error.message}`);
        updateStatus('disconnected', 'Connection failed');
        connectBtn.disabled = false;
        document.getElementById('connect-icon').textContent = '🔌';
        document.getElementById('connect-text').textContent = 'Connect & Talk';
    }
}

/**
 * Connect to Gemini Live API using JavaScript SDK
 */
async function connectToLiveAPI(functionDeclarations) {
    try {
        // Initialize Google GenAI client with ephemeral token
        // Must use v1alpha for ephemeral token support
        const ai = new GoogleGenAI({ 
            apiKey: ephemeralToken,
            httpOptions: { apiVersion: 'v1alpha' }
        });
        
        // Prepare tools configuration
        const tools = functionDeclarations.map(func => ({
            functionDeclarations: [func]
        }));
        
        // Configure session with native audio
        const config = {
            responseModalities: [Modality.AUDIO],
            speechConfig: {
                voiceConfig: {
                    prebuiltVoiceConfig: {
                        voiceName: 'Achird'
                    }
                }
            },
            systemInstruction: {
                parts: [{
                    text: "You are a helpful AI assistant with access to a knowledge base. When users ask questions, search the knowledge base using the search_knowledge_base function to find relevant information. Provide accurate, helpful answers based on the retrieved information. You can understand and respond in multiple languages automatically. Be friendly and conversational."
                }]
            },
            tools: tools
        };
        
        console.log('Connecting to Live API with JavaScript SDK...');
        
        // Connect using SDK with callbacks
        liveSession = await ai.live.connect({
            model: MODEL,
            callbacks: {
                onopen: function() {
                    console.log('Live session opened');
                    updateStatus('connected', 'Connected');
                    addTranscriptMessage('system', 'Connected! Microphone starting...');
                    
                    isConnected = true;
                    connectBtn.disabled = false;
                    document.getElementById('connect-icon').textContent = '⏹️';
                    document.getElementById('connect-text').textContent = 'Disconnect';
                    
                    // Auto-start recording
                    setTimeout(() => {
                        startRecording();
                    }, 500);
                },
                onmessage: function(message) {
                    console.log('[SDK] Received message:', message);
                    console.log('[SDK] Message type:', Object.keys(message));
                    responseQueue.push(message);
                    handleSDKMessage(message);
                },
                onerror: function(error) {
                    console.error('[SDK] Live session error:', error);
                    console.error('[SDK] Error type:', typeof error);
                    console.error('[SDK] Error details:', JSON.stringify(error, null, 2));
                    addTranscriptMessage('error', `Error: ${error.message || 'Unknown error'}`);
                },
                onclose: function(event) {
                    console.log('[SDK] Live session closed:', event);
                    console.log('[SDK] Close code:', event?.code);
                    console.log('[SDK] Close reason:', event?.reason);
                    console.log('[SDK] Was clean:', event?.wasClean);
                    const reason = event && event.reason ? event.reason : `Connection closed (code: ${event?.code})`;
                    addTranscriptMessage('system', reason);
                    handleDisconnect();
                }
            },
            config: config
        });
        
        console.log('Live session connected successfully');
        
    } catch (error) {
        console.error('Failed to connect to Live API:', error);
        throw error;
    }
}

/**
 * Handle messages from the JavaScript SDK
 */
async function handleSDKMessage(message) {
    try {
        console.log('[MSG] Processing message type:', Object.keys(message));
        
        // Handle setup complete
        if (message.setupComplete) {
            console.log('[MSG] ✓ Setup complete');
            return;
        }
        
        // Handle server content (model responses)
        if (message.serverContent) {
            const content = message.serverContent;
            console.log('[MSG] Server content keys:', Object.keys(content));
            
            // Check if model is starting to think/generate
            if (content.modelTurn && !content.modelTurn.parts) {
                console.log('[THINKING] 💭 Model is thinking...');
            }
            
            // Handle model turn with parts
            if (content.modelTurn && content.modelTurn.parts) {
                console.log('[MSG] Model turn with', content.modelTurn.parts.length, 'parts');
                console.log('[THINKING] ✓ Model generated response');
                for (const part of content.modelTurn.parts) {
                    console.log('[MSG] Part type:', Object.keys(part));
                    
                    // Handle text response
                    if (part.text) {
                        console.log('[MSG] ✓ Model text:', part.text);
                        addTranscriptMessage('assistant', part.text);
                    }
                    
                    // Handle function call
                    if (part.functionCall) {
                        console.log('[MSG] ✓ Function call:', part.functionCall);
                        await handleFunctionCall(part.functionCall);
                    }
                    
                    // Handle inline audio data
                    if (part.inlineData && part.inlineData.mimeType && part.inlineData.mimeType.startsWith('audio/')) {
                        console.log('[AUDIO] ✓ Received audio chunk');
                        console.log('[AUDIO] mimeType:', part.inlineData.mimeType);
                        console.log('[AUDIO] data length (base64):', part.inlineData.data.length);
                        playAudioChunk(part.inlineData.data);
                    } else if (part.inlineData) {
                        console.log('[MSG] InlineData without audio, mimeType:', part.inlineData.mimeType);
                    }
                }
            } else {
                console.log('[MSG] No modelTurn or parts in serverContent');
            }
            
            // Handle turn complete
            if (content.turnComplete) {
                console.log('[MSG] ✓ Turn complete');
            }
            
            // Handle interruption
            if (content.interrupted) {
                console.log('[MSG] ⚠ Generation interrupted');
                stopAudioPlayback();
            }
        }
        
        // Handle tool calls (alternative format)
        if (message.toolCall) {
            console.log('[MSG] ✓ Tool call message:', message.toolCall);
            if (message.toolCall.functionCalls) {
                for (const fc of message.toolCall.functionCalls) {
                    await handleFunctionCall(fc);
                }
            }
        }
        
        // Check if message is empty
        if (!message.setupComplete && !message.serverContent && !message.toolCall) {
            console.warn('[MSG] ⚠ Received message with no recognized content');
        }
    } catch (error) {
        console.error('[MSG] ✗ Error handling SDK message:', error);
        console.error('[MSG] Error stack:', error.stack);
    }
}

/**
 * Handle function calls from the model
 */
async function handleFunctionCall(functionCall) {
    const { name, args, id } = functionCall;
    
    // Display the search query in transcript
    const query = args.query || 'knowledge base';
    addTranscriptMessage('system', `🔍 Searching knowledge base for: "${query}"`);
    console.log('[FUNCTION] Search query:', query);
    
    try {
        // Call our backend API to execute the function
        const response = await fetch(`${API_BASE_URL}/api/search-knowledge-base`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(args)
        });
        
        if (!response.ok) {
            throw new Error('Function call failed');
        }
        
        const result = await response.json();
        
        // Send function response back to the model using SDK
        const functionResponses = [{
            id: id,
            name: name,
            response: result
        }];
        
        if (liveSession && liveSession.sendToolResponse) {
            await liveSession.sendToolResponse({ functionResponses: functionResponses });
        }
        
        addTranscriptMessage('system', `✓ Found ${result.count} relevant sources`);
        
    } catch (error) {
        console.error('Function call error:', error);
        
        // Send error response
        const errorFunctionResponses = [{
            id: id,
            name: name,
            response: {
                error: error.message
            }
        }];
        
        if (liveSession && liveSession.sendToolResponse) {
            await liveSession.sendToolResponse({ functionResponses: errorFunctionResponses });
        }
        
        addTranscriptMessage('error', `Function call failed: ${error.message}`);
    }
}

/**
 * Start audio recording
 */
async function startRecording() {
    try {
        console.log('[INPUT] Starting recording...');
        console.log('[INPUT] Live session available:', !!liveSession);
        console.log('[INPUT] sendRealtimeInput method:', !!liveSession?.sendRealtimeInput);
        console.log('[INPUT] sendToolResponse method:', !!liveSession?.sendToolResponse);
        
        // Request microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: SEND_SAMPLE_RATE,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        console.log('[INPUT] ✓ Microphone access granted');
        console.log('[INPUT] Audio tracks:', audioStream.getAudioTracks().length);
        
        // Create audio context for processing if not exists
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: SEND_SAMPLE_RATE
            });
            console.log('[INPUT] Created audio context');
        }
        
        const source = audioContext.createMediaStreamSource(audioStream);
        
        // Use ScriptProcessorNode (deprecated but widely supported)
        // TODO: Migrate to AudioWorkletNode when browser support improves
        audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        
        let audioChunksSent = 0;
        let userSpeakingDetected = false;
        
        audioProcessor.onaudioprocess = (e) => {
            if (!isRecording) return;
            
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = convertToPCM16(inputData);
            
            // Calculate audio level for monitoring
            const rms = Math.sqrt(inputData.reduce((sum, val) => sum + val * val, 0) / inputData.length);
            
            // Detect if user is speaking (simple threshold-based detection)
            const isSpeaking = rms > VAD_THRESHOLD;
            
            // If user starts speaking, stop any ongoing audio playback (interruption)
            if (isSpeaking && !userSpeakingDetected) {
                userSpeakingDetected = true;
                stopAudioPlayback();
                console.log('[INPUT] 🎤 User speaking detected - interrupting playback');
            } else if (!isSpeaking && userSpeakingDetected) {
                userSpeakingDetected = false;
                console.log('[INPUT] 🔇 User stopped speaking');
            }
            
            // Send audio to Live API using SDK
            if (liveSession && liveSession.sendRealtimeInput) {
                try {
                    const base64Audio = arrayBufferToBase64(pcmData);
                    liveSession.sendRealtimeInput({
                        audio: {
                            data: base64Audio,
                            mimeType: 'audio/pcm;rate=16000'
                        }
                    });
                    audioChunksSent++;
                    
                    // Log every 50 chunks (roughly every 3 seconds)
                    if (audioChunksSent % 50 === 0) {
                        console.log(`[INPUT] ✓ Sent ${audioChunksSent} audio chunks, RMS level: ${rms.toFixed(4)}`);
                    }
                } catch (error) {
                    console.error('[INPUT] ✗ Error sending audio:', error);
                    console.error('[INPUT] Error details:', error.stack);
                }
            } else {
                if (audioChunksSent === 0) {
                    console.error('[INPUT] ✗ Cannot send audio - liveSession or sendRealtimeInput method not available');
                    console.error('[INPUT] liveSession exists:', !!liveSession);
                    console.error('[INPUT] Available methods:', liveSession ? Object.keys(liveSession) : 'none');
                }
            }
            
            // Update visualizer
            drawVisualizerActive(inputData);
        };
        
        source.connect(audioProcessor);
        audioProcessor.connect(audioContext.destination);
        
        isRecording = true;
        updateStatus('connected', '🎤 Recording...');
        addTranscriptMessage('system', '🎤 Recording started - speak now!');
        
        console.log('[INPUT] ✓ Recording pipeline established');
        console.log('[INPUT] Audio processing started, will send chunks to Live API');
        
    } catch (error) {
        console.error('[INPUT] ✗ Recording error:', error);
        console.error('[INPUT] Error stack:', error.stack);
        addTranscriptMessage('error', `Microphone access failed: ${error.message}`);
    }
}

/**
 * Stop audio recording
 */
function stopRecording() {
    isRecording = false;
    
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
    
    if (audioProcessor) {
        audioProcessor.disconnect();
        audioProcessor = null;
    }
    
    drawVisualizerIdle();
}

/**
 * Handle disconnect
 */
function handleDisconnect() {
    console.log('[DISCONNECT] Starting disconnect process');
    console.log('[DISCONNECT] isRecording:', isRecording);
    console.log('[DISCONNECT] liveSession exists:', !!liveSession);
    
    if (isRecording) {
        stopRecording();
    }
    
    if (liveSession) {
        try {
            liveSession.close();
            console.log('[DISCONNECT] ✓ Live session closed');
        } catch (error) {
            console.error('[DISCONNECT] ✗ Error closing live session:', error);
        }
        liveSession = null;
    }
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
        console.log('[DISCONNECT] ✓ Audio context closed');
    }
    
    audioQueueTime = 0;
    isConnected = false;
    isRecording = false;
    responseQueue = [];
    
    updateStatus('disconnected', 'Disconnected');
    connectBtn.disabled = false;
    document.getElementById('connect-icon').textContent = '🔌';
    document.getElementById('connect-text').textContent = 'Connect & Talk';
    
    if (!transcript.querySelector('.system-message')) {
        addTranscriptMessage('system', 'Disconnected from Live API');
    }
    
    console.log('[DISCONNECT] ✓ Disconnect complete');
}

/**
 * Convert Float32Array to PCM16 Int16Array
 */
function convertToPCM16(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
        const s = Math.max(-1, Math.min(1, float32Array[i]));
        int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array.buffer;
}

/**
 * Convert ArrayBuffer to Base64
 */
function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

/**
 * Play audio chunk from model response
 * Uses queued playback for smooth audio without gaps
 */
function playAudioChunk(base64Data) {
    console.log('[OUTPUT] ✓ playAudioChunk called, base64 length:', base64Data.length);
    
    if (!audioContext) {
        // Create playback-only audio context if needed
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: RECEIVE_SAMPLE_RATE
        });
        console.log('[OUTPUT] Created new audio context for playback');
    }
    
    try {
        // Decode base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        console.log('[OUTPUT] Decoded audio bytes:', bytes.length);
        
        // Ensure buffer length is even for Int16Array (2 bytes per sample)
        const byteLength = bytes.length - (bytes.length % 2);
        
        if (byteLength !== bytes.length) {
            console.warn(`[OUTPUT] ⚠ Buffer length adjusted from ${bytes.length} to ${byteLength} (odd byte)`);
        }
        
        // Create Int16Array directly from the buffer
        // PCM data from Gemini is always little-endian, which matches most systems
        const int16Array = new Int16Array(bytes.buffer, bytes.byteOffset, byteLength / 2);
        
        // Convert PCM16 to Float32 for Web Audio API
        const float32Array = new Float32Array(int16Array.length);
        for (let i = 0; i < int16Array.length; i++) {
            // Normalize int16 to [-1, 1] range
            float32Array[i] = int16Array[i] / 32768.0;
        }
        
        // Sample first few values to check if they look reasonable
        const samples = float32Array.slice(0, 10);
        console.log('[OUTPUT] First 10 audio samples:', samples);
        const max = Math.max(...float32Array.map(Math.abs));
        const rms = Math.sqrt(float32Array.reduce((sum, val) => sum + val * val, 0) / float32Array.length);
        console.log('[OUTPUT] Max amplitude:', max, ', RMS:', rms);
        
        if (max === 0) {
            console.warn('[OUTPUT] ⚠ Audio buffer is silent (all zeros)');
        }
        
        // Create audio buffer with correct sample rate (24kHz for output)
        const audioBuffer = audioContext.createBuffer(1, float32Array.length, RECEIVE_SAMPLE_RATE);
        audioBuffer.copyToChannel(float32Array, 0);
        
        // Queue and schedule playback for smooth continuous audio
        const now = audioContext.currentTime;
        if (audioQueueTime < now) {
            audioQueueTime = now;
        }
        
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start(audioQueueTime);
        
        // Track active sources for interruption
        if (!window.activeSources) {
            window.activeSources = [];
        }
        window.activeSources.push(source);
        
        // Clean up when done
        source.onended = () => {
            const index = window.activeSources.indexOf(source);
            if (index > -1) {
                window.activeSources.splice(index, 1);
            }
        };
        
        // Update queue time for next chunk
        audioQueueTime += audioBuffer.duration;
        
        console.log(`[OUTPUT] ✓ Playing audio: ${int16Array.length} samples (${(int16Array.length/RECEIVE_SAMPLE_RATE).toFixed(3)}s), queued at ${audioQueueTime.toFixed(3)}s`);
        
    } catch (error) {
        console.error('[OUTPUT] ✗ Audio playback error:', error);
        console.error('[OUTPUT] Error stack:', error.stack);
    }
}

/**
 * Stop audio playback (for interruptions)
 * This handles user interruptions to prevent overlapping audio
 */
function stopAudioPlayback() {
    // Stop all currently playing audio sources
    if (window.activeSources && window.activeSources.length > 0) {
        console.log(`[OUTPUT] ⏹️ Stopping ${window.activeSources.length} active audio sources`);
        window.activeSources.forEach(source => {
            try {
                source.stop();
            } catch (e) {
                // Source may have already stopped
            }
        });
        window.activeSources = [];
    }
    
    // Reset the audio queue time to stop scheduling future chunks
    audioQueueTime = 0;
    console.log('[OUTPUT] ✓ Audio playback interrupted and cleared');
}

/**
 * Draw visualizer in idle state
 */
function drawVisualizerIdle() {
    canvasContext.fillStyle = '#f9f9f9';
    canvasContext.fillRect(0, 0, visualizer.width, visualizer.height);
    
    canvasContext.strokeStyle = '#ddd';
    canvasContext.lineWidth = 2;
    canvasContext.beginPath();
    canvasContext.moveTo(0, visualizer.height / 2);
    canvasContext.lineTo(visualizer.width, visualizer.height / 2);
    canvasContext.stroke();
}

/**
 * Draw visualizer with active audio
 */
function drawVisualizerActive(dataArray) {
    canvasContext.fillStyle = '#f9f9f9';
    canvasContext.fillRect(0, 0, visualizer.width, visualizer.height);
    
    const sliceWidth = visualizer.width / dataArray.length;
    let x = 0;
    
    canvasContext.strokeStyle = '#667eea';
    canvasContext.lineWidth = 2;
    canvasContext.beginPath();
    
    for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i];
        const y = (v + 1) * visualizer.height / 2;
        
        if (i === 0) {
            canvasContext.moveTo(x, y);
        } else {
            canvasContext.lineTo(x, y);
        }
        
        x += sliceWidth;
    }
    
    canvasContext.stroke();
}
