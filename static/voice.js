/**
 * Live Voice RAG - JavaScript client for Gemini Live API with native audio
 * Uses JavaScript SDK (@google/genai) with ephemeral tokens for secure authentication
 * 
 * IMPORTANT: Ephemeral tokens require v1alpha API version. Initialize client with:
 *   new GoogleGenAI({ apiKey: token, httpOptions: { apiVersion: 'v1alpha' } })
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
                    console.log('Received message:', message);
                    responseQueue.push(message);
                    handleSDKMessage(message);
                },
                onerror: function(error) {
                    console.error('Live session error:', error);
                    addTranscriptMessage('error', `Error: ${error.message || 'Unknown error'}`);
                },
                onclose: function(event) {
                    console.log('Live session closed:', event);
                    const reason = event && event.reason ? event.reason : 'Connection closed';
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
        // Handle setup complete
        if (message.setupComplete) {
            console.log('Setup complete');
            return;
        }
        
        // Handle server content (model responses)
        if (message.serverContent) {
            const content = message.serverContent;
            
            // Handle model turn with parts
            if (content.modelTurn && content.modelTurn.parts) {
                for (const part of content.modelTurn.parts) {
                    // Handle text response
                    if (part.text) {
                        console.log('Model text:', part.text);
                        addTranscriptMessage('assistant', part.text);
                    }
                    
                    // Handle function call
                    if (part.functionCall) {
                        console.log('Function call:', part.functionCall);
                        await handleFunctionCall(part.functionCall);
                    }
                    
                    // Handle inline audio data
                    if (part.inlineData && part.inlineData.mimeType && part.inlineData.mimeType.startsWith('audio/')) {
                        if (DEBUG_AUDIO) {
                            console.log('Received audio chunk, mimeType:', part.inlineData.mimeType);
                            console.log('Audio data length (base64):', part.inlineData.data.length);
                        }
                        playAudioChunk(part.inlineData.data);
                    }
                }
            }
            
            // Handle turn complete
            if (content.turnComplete) {
                console.log('Turn complete');
            }
            
            // Handle interruption
            if (content.interrupted) {
                console.log('Generation interrupted');
                stopAudioPlayback();
            }
        }
        
        // Handle tool calls (alternative format)
        if (message.toolCall) {
            console.log('Tool call message:', message.toolCall);
            if (message.toolCall.functionCalls) {
                for (const fc of message.toolCall.functionCalls) {
                    await handleFunctionCall(fc);
                }
            }
        }
    } catch (error) {
        console.error('Error handling SDK message:', error);
    }
}

/**
 * Handle function calls from the model
 */
async function handleFunctionCall(functionCall) {
    const { name, args, id } = functionCall;
    
    addTranscriptMessage('system', `🔍 Searching knowledge base...`);
    
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
        // Request microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: SEND_SAMPLE_RATE,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        // Create audio context for processing if not exists
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: SEND_SAMPLE_RATE
            });
        }
        
        const source = audioContext.createMediaStreamSource(audioStream);
        
        // Use ScriptProcessorNode (deprecated but widely supported)
        // TODO: Migrate to AudioWorkletNode when browser support improves
        audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        
        audioProcessor.onaudioprocess = (e) => {
            if (!isRecording) return;
            
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = convertToPCM16(inputData);
            
            // Send audio to Live API using SDK
            if (liveSession && liveSession.send) {
                try {
                    const base64Audio = arrayBufferToBase64(pcmData);
                    liveSession.send({
                        realtimeInput: {
                            mediaChunks: [{
                                mimeType: 'audio/pcm;rate=16000',
                                data: base64Audio
                            }]
                        }
                    });
                } catch (error) {
                    console.error('Error sending audio:', error);
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
        
    } catch (error) {
        console.error('Recording error:', error);
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
    if (isRecording) {
        stopRecording();
    }
    
    if (liveSession) {
        try {
            liveSession.close();
        } catch (error) {
            console.error('Error closing live session:', error);
        }
        liveSession = null;
    }
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
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
    if (!audioContext) {
        // Create playback-only audio context if needed
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: RECEIVE_SAMPLE_RATE
        });
    }
    
    try {
        // Decode base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Ensure buffer length is even for Int16Array (2 bytes per sample)
        const byteLength = bytes.length - (bytes.length % 2);
        
        if (DEBUG_AUDIO && byteLength !== bytes.length) {
            console.warn(`Buffer length adjusted from ${bytes.length} to ${byteLength} (odd byte)`);
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
        
        if (DEBUG_AUDIO) {
            // Sample first few values to check if they look reasonable
            const samples = float32Array.slice(0, 10);
            console.log('First 10 audio samples:', samples);
            const max = Math.max(...float32Array.map(Math.abs));
            console.log('Max amplitude:', max);
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
        
        // Update queue time for next chunk
        audioQueueTime += audioBuffer.duration;
        
        console.log(`Playing audio chunk: ${int16Array.length} samples (${(int16Array.length/RECEIVE_SAMPLE_RATE).toFixed(3)}s), queued at ${audioQueueTime.toFixed(3)}s`);
        
    } catch (error) {
        console.error('Audio playback error:', error);
    }
}

/**
 * Stop audio playback (for interruptions)
 */
function stopAudioPlayback() {
    // Reset the audio queue time to stop scheduling future chunks
    audioQueueTime = 0;
    console.log('Audio playback interrupted');
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
