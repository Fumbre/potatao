'''
Faster-Whisper + strategy pattern
'''
# ABC = Abstract Base Class
from abc import ABC, abstractmethod

# allows you to create files in memory (RAM)
import io

# Base interface 
# Every transcriber must implement this: swap implementations in server.py
class BaseTranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Receives raw audio bytes (WAV or PCM) and returns the transcribed text.
        """
        pass 


# Faster-Whisper (local) 
class FasterWhisperTranscriber(BaseTranscriber):
    def __init__(self, model_size: str = "base"):
        """
        @param model_size  Whisper model to load: tiny, base, small, medium, large
                           Larger = more accurate but slower and more RAM
                           Recommended for Pi Zero pipeline: "base" or "small"
        """
        from faster_whisper import WhisperModel

        print(f"[Transcriber] Loading Faster-Whisper model: {model_size}")

        # device="cpu" because this runs on a regular PC without GPU requirement # 
        # compute_type="int8" reduces RAM usage significantly with minimal quality loss
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8") 
        # TODO: some pc have the GPU on nvdia.

        print("[Transcriber] Model loaded.")

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribes audio bytes to text using Faster-Whisper.
        Audio must be WAV format (16-bit PCM, mono, 16kHz or 24kHz).
        """
        # Faster-Whisper expects a file path or file-like object
        audio_file = io.BytesIO(audio_bytes)

        # segments is a generator: iterate to get all transcribed text chunks
        segments, _ = self.model.transcribe(audio_file) 
        # TODO: how this recursion works?

        # Join all segments into a single string
        text = " ".join(segment.text for segment in segments).strip()

        print(f"[Transcriber] Transcribed: {text}")
        return text


# OpenAI Whisper API (cloud fallback) 
class OpenAITranscriber(BaseTranscriber):
    def __init__(self, api_key: str):
        """
        @param api_key  Your OpenAI API key (store in .env)
        """
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        print("[Transcriber] Using OpenAI Whisper API.")

    def transcribe(self, audio_bytes: bytes) -> str:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"  # OpenAI API requires a filename

        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

        text = response.text.strip()
        print(f"[Transcriber] Transcribed: {text}")
        return text
    
