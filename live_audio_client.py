#!/usr/bin/env python3
"""
Gemini Live API Audio Client
Continuous voice conversation client using pyaudio for real-time streaming.
Based on official Gemini Live API quickstart.

Usage:
    python live_audio_client.py --language en-IN
    python live_audio_client.py --language hi-IN
"""

import os
import asyncio
import argparse
import traceback
import pyaudio

from google import genai
from google.genai import types

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025"

# Initialize PyAudio
pya = pyaudio.PyAudio()


class LiveAudioClient:
    """
    Live audio client for continuous voice conversation.
    """
    
    def __init__(self, language: str = "en-IN"):
        """Initialize the audio client."""
        self.language = language
        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self.audio_stream = None
        
        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key
        )
        
        print(f"✓ Initialized Live Audio Client for {language}")
    
    def get_config(self) -> types.LiveConnectConfig:
        """Get Live API configuration with VAD and affective dialog."""
        language_name = "English (India)" if self.language == "en-IN" else "Hindi (India)"
        
        system_instruction = f"""You are a helpful AI assistant. 
Please respond in {language_name} language.
Be conversational and natural in your responses.
Keep responses concise and to the point."""
        
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Achird"
                    )
                )
            ),
            # Enable Voice Activity Detection for automatic turn-taking
            voice_activity_detection=types.VoiceActivityDetectionConfig(
                enabled=True
            ),
            # Enable affective dialog for natural emotional responses
            affective_dialog=types.AffectiveDialogConfig(
                enabled=True
            ),
            # Enable turn coverage for better conversation flow
            turn_coverage=types.TurnCoverageConfig(
                enabled=True
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
            system_instruction=system_instruction
        )
        
        return config
    
    async def listen_audio(self):
        """Capture audio from microphone and send to Live API."""
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        
        print("🎤 Microphone active - speak naturally, VAD will detect when you're talking")
        
        kwargs = {"exception_on_overflow": False}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
    
    async def send_realtime(self):
        """Send audio data to Live API in real-time."""
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)
    
    async def receive_audio(self):
        """Receive audio responses from Live API."""
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                if text := response.text:
                    print(f"🤖 AI: {text}")
            
            # Clear audio queue on turn complete (for interruptions)
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()
    
    async def play_audio(self):
        """Play audio responses through speakers."""
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        
        print("🔊 Speaker active - audio responses will play automatically")
        
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)
    
    async def run(self):
        """Run the live audio conversation."""
        try:
            print(f"\n{'='*60}")
            print(f"🎤 Gemini Live API - Continuous Voice Conversation")
            print(f"Language: {self.language}")
            print(f"{'='*60}")
            print("\nInstructions:")
            print("- Just speak naturally - Voice Activity Detection is enabled")
            print("- No need to click anything - it's like a phone call")
            print("- AI will respond with voice and text")
            print("- Press Ctrl+C to exit")
            print(f"{'='*60}\n")
            
            async with (
                self.client.aio.live.connect(model=MODEL, config=self.get_config()) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)
                
                # Start all tasks
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                
        except KeyboardInterrupt:
            print("\n\n👋 Ending conversation. Goodbye!")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
        finally:
            if self.audio_stream:
                self.audio_stream.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Gemini Live API Audio Client")
    parser.add_argument(
        "--language",
        type=str,
        default="en-IN",
        choices=["en-IN", "hi-IN"],
        help="Language for conversation (en-IN for English India, hi-IN for Hindi India)"
    )
    args = parser.parse_args()
    
    client = LiveAudioClient(language=args.language)
    asyncio.run(client.run())


if __name__ == "__main__":
    main()
