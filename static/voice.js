/**
 * Live Voice RAG - JavaScript client for Gemini Live API with native audio
 * Uses ephemeral tokens for secure client-side authentication
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const GEMINI_API_BASE = 'https://generativelanguage.googleapis.com';
const MODEL = 'gemini-2.5-flash-native-audio-preview-09-2025';

// Audio Configuration
const SEND_SAMPLE_RATE = 16000;
const RECEIVE_SAMPLE_RATE = 24000;

// State
let websocket = null;
let ephemeralToken = null;
let mediaRecorder = null;
let audioContext = null;
let audioStream = null;
let isRecording = false;
let audioPlaybackQueue = [];
let isPlaying = false;

// UI Elements
const connectBtn = document.getElementById('connect-btn');
const micBtn = document.getElementById('mic-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const transcript = document.getElementById('transcript');
const visualizer = document.getElementById('visualizer');
const canvasContext = visualizer.getContext('2d');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    connectBtn.addEventListener('click', handleConnect);
    micBtn.addEventListener('click', handleMicToggle);
    disconnectBtn.addEventListener('click', handleDisconnect);
    
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
 * Handle Connect button
 */
async function handleConnect() {
    try {
        updateStatus('connecting', 'Connecting...');
        connectBtn.disabled = true;
        
        // Clear transcript
        transcript.innerHTML = '<p class="system-message">Connecting to Live API...</p>';
        
        // Get ephemeral token from backend
        const tokenResponse = await fetch(`${API_BASE_URL}/api/generate-token`);
        if (!tokenResponse.ok) {
            throw new Error('Failed to get ephemeral token');
        }
        
        const tokenData = await tokenResponse.json();
        ephemeralToken = tokenData.token;
        
        addTranscriptMessage('system', 'Token obtained, establishing WebSocket connection...');
        
        // Get function declarations
        const functionsResponse = await fetch(`${API_BASE_URL}/api/function-declarations`);
        const functionsData = await functionsResponse.json();
        
        // Connect to Gemini Live API using WebSocket
        await connectToLiveAPI(functionsData.functions);
        
    } catch (error) {
        console.error('Connection error:', error);
        addTranscriptMessage('error', `Connection failed: ${error.message}`);
        updateStatus('disconnected', 'Connection failed');
        connectBtn.disabled = false;
    }
}

/**
 * Connect to Gemini Live API via WebSocket
 */
async function connectToLiveAPI(functionDeclarations) {
    return new Promise((resolve, reject) => {
        const wsUrl = `${GEMINI_API_BASE}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${ephemeralToken}`;
        
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
            console.log('WebSocket connected');
            
            // Send setup message with native audio configuration
            const setupMessage = {
                setup: {
                    model: `models/${MODEL}`,
                    generation_config: {
                        response_modalities: ['AUDIO'],
                        speech_config: {
                            voice_config: {
                                prebuilt_voice_config: {
                                    voice_name: 'Achird'
                                }
                            }
                        }
                    },
                    system_instruction: {
                        parts: [{
                            text: "You are a helpful AI assistant with access to a knowledge base. When users ask questions, search the knowledge base using the search_knowledge_base function to find relevant information. Provide accurate, helpful answers based on the retrieved information. You can understand and respond in multiple languages automatically. Be friendly and conversational."
                        }]
                    },
                    tools: functionDeclarations.map(func => ({
                        function_declarations: [func]
                    }))
                }
            };
            
            websocket.send(JSON.stringify(setupMessage));
            
            updateStatus('connected', 'Connected');
            addTranscriptMessage('system', 'Connected! You can now start talking.');
            
            micBtn.disabled = false;
            disconnectBtn.disabled = false;
            
            resolve();
        };
        
        websocket.onmessage = async (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('Received message:', message);
                
                await handleServerMessage(message);
            } catch (error) {
                console.error('Error handling message:', error);
            }
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            addTranscriptMessage('error', 'WebSocket error occurred');
            reject(error);
        };
        
        websocket.onclose = () => {
            console.log('WebSocket closed');
            updateStatus('disconnected', 'Disconnected');
            connectBtn.disabled = false;
            micBtn.disabled = true;
            disconnectBtn.disabled = true;
        };
    });
}

/**
 * Handle messages from the server
 */
async function handleServerMessage(message) {
    // Handle setup complete
    if (message.setupComplete) {
        console.log('Setup complete');
        return;
    }
    
    // Handle server content (model responses)
    if (message.serverContent) {
        const content = message.serverContent;
        
        // Handle tool calls
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
                if (part.inlineData && part.inlineData.mimeType === 'audio/pcm') {
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
        
        // Send function response back to the model
        const functionResponse = {
            toolResponse: {
                functionResponses: [{
                    id: id,
                    name: name,
                    response: result
                }]
            }
        };
        
        websocket.send(JSON.stringify(functionResponse));
        
        addTranscriptMessage('system', `✓ Found ${result.count} relevant sources`);
        
    } catch (error) {
        console.error('Function call error:', error);
        
        // Send error response
        const errorResponse = {
            toolResponse: {
                functionResponses: [{
                    id: id,
                    name: name,
                    response: {
                        error: error.message
                    }
                }]
            }
        };
        
        websocket.send(JSON.stringify(errorResponse));
        
        addTranscriptMessage('error', `Function call failed: ${error.message}`);
    }
}

/**
 * Handle microphone toggle
 */
async function handleMicToggle() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
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
        
        // Create audio context for processing
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: SEND_SAMPLE_RATE
        });
        
        const source = audioContext.createMediaStreamSource(audioStream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        processor.onaudioprocess = (e) => {
            if (!isRecording) return;
            
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = convertToPCM16(inputData);
            
            // Send audio to Live API
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                const audioMessage = {
                    realtimeInput: {
                        mediaChunks: [{
                            mimeType: 'audio/pcm;rate=16000',
                            data: arrayBufferToBase64(pcmData)
                        }]
                    }
                };
                
                websocket.send(JSON.stringify(audioMessage));
            }
            
            // Update visualizer
            drawVisualizerActive(inputData);
        };
        
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        isRecording = true;
        micBtn.classList.add('recording');
        document.getElementById('mic-icon').textContent = '🔴';
        document.getElementById('mic-text').textContent = 'Stop Talking';
        
        addTranscriptMessage('system', '🎤 Recording started...');
        
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
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    
    micBtn.classList.remove('recording');
    document.getElementById('mic-icon').textContent = '🎤';
    document.getElementById('mic-text').textContent = 'Start Talking';
    
    drawVisualizerIdle();
    
    addTranscriptMessage('system', '🛑 Recording stopped');
}

/**
 * Handle disconnect
 */
function handleDisconnect() {
    if (isRecording) {
        stopRecording();
    }
    
    if (websocket) {
        websocket.close();
        websocket = null;
    }
    
    stopAudioPlayback();
    
    updateStatus('disconnected', 'Disconnected');
    connectBtn.disabled = false;
    micBtn.disabled = true;
    disconnectBtn.disabled = true;
    
    addTranscriptMessage('system', 'Disconnected from Live API');
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
 */
function playAudioChunk(base64Data) {
    audioPlaybackQueue.push(base64Data);
    if (!isPlaying) {
        playNextAudioChunk();
    }
}

/**
 * Play next audio chunk from queue
 */
async function playNextAudioChunk() {
    if (audioPlaybackQueue.length === 0) {
        isPlaying = false;
        return;
    }
    
    isPlaying = true;
    const base64Data = audioPlaybackQueue.shift();
    
    try {
        // Decode base64 to ArrayBuffer
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Create audio context if not exists
        if (!audioContext || audioContext.state === 'closed') {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: RECEIVE_SAMPLE_RATE
            });
        }
        
        // Convert PCM16 to Float32
        const int16Array = new Int16Array(bytes.buffer);
        const float32Array = new Float32Array(int16Array.length);
        for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
        }
        
        // Create audio buffer
        const audioBuffer = audioContext.createBuffer(1, float32Array.length, RECEIVE_SAMPLE_RATE);
        audioBuffer.getChannelData(0).set(float32Array);
        
        // Play audio
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.onended = () => {
            playNextAudioChunk();
        };
        source.start();
        
    } catch (error) {
        console.error('Audio playback error:', error);
        playNextAudioChunk(); // Continue with next chunk
    }
}

/**
 * Stop audio playback
 */
function stopAudioPlayback() {
    audioPlaybackQueue = [];
    isPlaying = false;
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
