"""
Text-to-Speech service using Gemini TTS API.
"""

import base64
import mimetypes
import struct
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings
from app.utils.logging_config import app_logger, error_logger


class TTSService:
    """
    Text-to-Speech service using Gemini TTS.
    """

    def __init__(self):
        """Initialize TTS service."""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_tts_model
        app_logger.info(f"Initialized TTSService with model: {self.model}")

    def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert to speech

        Returns:
            Audio data as bytes in WAV format, or None if failed
        """
        try:
            app_logger.info(f"Converting text to speech: {text[:50]}...")

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=text),
                    ],
                ),
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=["audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
                    )
                ),
            )

            audio_data = b""
            mime_type = None

            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                if (
                    chunk.candidates[0].content.parts[0].inline_data
                    and chunk.candidates[0].content.parts[0].inline_data.data
                ):
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    audio_data += inline_data.data
                    if mime_type is None:
                        mime_type = inline_data.mime_type

            if audio_data and mime_type:
                # Convert to WAV format
                wav_data = self._convert_to_wav(audio_data, mime_type)
                app_logger.info(
                    f"Successfully converted text to speech, audio size: {len(wav_data)} bytes"
                )
                return wav_data
            else:
                app_logger.warning("No audio data generated")
                return None

        except Exception as e:
            error_logger.error(f"Failed to convert text to speech: {e}")
            return None

    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """
        Convert audio data to WAV format.

        Args:
            audio_data: Raw audio data
            mime_type: MIME type of audio data

        Returns:
            WAV formatted audio data
        """
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",  # ChunkID
            chunk_size,  # ChunkSize
            b"WAVE",  # Format
            b"fmt ",  # Subchunk1ID
            16,  # Subchunk1Size
            1,  # AudioFormat (PCM)
            num_channels,  # NumChannels
            sample_rate,  # SampleRate
            byte_rate,  # ByteRate
            block_align,  # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",  # Subchunk2ID
            data_size,  # Subchunk2Size
        )

        return header + audio_data

    def _parse_audio_mime_type(self, mime_type: str) -> dict:
        """
        Parse bits per sample and rate from audio MIME type.

        Args:
            mime_type: Audio MIME type string

        Returns:
            Dictionary with bits_per_sample and rate
        """
        bits_per_sample = 16
        rate = 24000

        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass

        return {"bits_per_sample": bits_per_sample, "rate": rate}
