'''
Piper + ElevenLabs + strategy pattern
'''
from abc import ABC, abstractmethod


class BaseTTS(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str) -> bytes:
        """
        Receives translated text and target language.
        Returns audio as raw bytes (WAV format).
        """
        pass


class PiperTTS(BaseTTS):
    """
    Lightweight local TTS designed for low resource devices.
    Sounds decent, fully offline, no API key needed.

    Installation:
        pip install piper-tts

    Models are downloaded automatically on first use.
    Voice list: https://rhasspy.github.io/piper-samples/
    """

    # Maps language names to Piper voice model names
    # Add more as needed: https://rhasspy.github.io/piper-samples/
    VOICE_MAP = {
        "English":    "en_US-r-medium",
        "French":     "fr_FR-upmc-medium",
        "German":     "de_DE-thorsten-medium",
        "Spanish":    "es_ES-carlfm-x_low",
        "Dutch":      "nl_NL-mls-medium",
        "Italian":    "it_IT-riccardo-x_low",
        "Portuguese": "pt_PT-tugao-medium",
        "Ukrainian":  "uk_UA-lada-x_low",
        "Russian":    "ru_RU-ruslan-medium",
        "Polish":     "pl_PL-mls-medium",
    }

    # Default voice used when the target language has no mapping
    DEFAULT_VOICE = "en_US-lessac-medium"

    def __init__(self):
        from piper.voice import PiperVoice
        self._PiperVoice = PiperVoice
        self._loaded_voices = {}  # cache: avoid reloading the same voice twice
        print("[TTS] Using Piper TTS (local).")

    def _get_voice(self, language: str):
        """Loads and caches the voice model for the given language."""
        voice_name = self.VOICE_MAP.get(language, self.DEFAULT_VOICE)

        if voice_name not in self._loaded_voices:
            print(f"[TTS] Loading Piper voice: {voice_name}")
            self._loaded_voices[voice_name] = self._PiperVoice.load(voice_name)

        return self._loaded_voices[voice_name]

    def synthesize(self, text: str, language: str) -> bytes:
        import io
        import wave

        voice = self._get_voice(language)

        # Piper writes audio to a WAV file-like object
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            voice.synthesize(text, wav_file)

        print(f"[TTS] Synthesized {len(wav_buffer.getvalue())} bytes (Piper, {language})")
        return wav_buffer.getvalue()


class ElevenLabsTTS(BaseTTS):
    """
    High quality cloud TTS with very natural intonation.
    Requires an ElevenLabs API key, free tier available.

    Installation:
        pip install elevenlabs

    Voice IDs: https://api.elevenlabs.io/v1/voices
    """

    # Maps language names to ElevenLabs voice IDs
    # These are multilingual voices that support many languages
    VOICE_MAP = {
        "English":    "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "French":     "ThT5KcBeYPX3keUQqHPh",  # Dorothy (multilingual)
        "German":     "ThT5KcBeYPX3keUQqHPh",
        "Spanish":    "ThT5KcBeYPX3keUQqHPh",
        "Dutch":      "ThT5KcBeYPX3keUQqHPh",
        "Italian":    "ThT5KcBeYPX3keUQqHPh",
        "Portuguese": "ThT5KcBeYPX3keUQqHPh",
        "Ukrainian":  "ThT5KcBeYPX3keUQqHPh",
    }

    DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"

    def __init__(self, api_key: str):
        """
        api_key         ElevenLabs API key (store in .env, never hardcode)
        """
        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=api_key)
        print("[TTS] Using ElevenLabs TTS (cloud).")

    def synthesize(self, text: str, language: str) -> bytes:
        voice_id = self.VOICE_MAP.get(language, self.DEFAULT_VOICE)

        # generate() returns an iterator of audio chunks
        audio_chunks = self.client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2"  # supports all languages
        )

        # Concatenate all chunks into a single bytes object
        audio_bytes = b"".join(audio_chunks)

        print(f"[TTS] Synthesized {len(audio_bytes)} bytes (ElevenLabs, {language})")
        return audio_bytes


class OpenAITTS(BaseTTS):
    """
    Very natural cloud TTS from OpenAI.
    Cheap (~$15 per 1M characters), supports all languages automatically.

    Installation:
        pip install openai
    """

    def __init__(self, api_key: str, voice: str = "nova"):
        """
        api_key  OpenAI API key
        voice    Voice to use: alloy, echo, fable, onyx, nova, shimmer
        """
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.voice  = voice
        print(f"[TTS] Using OpenAI TTS (cloud), voice: {voice}.")

    def synthesize(self, text: str, language: str) -> bytes:
        # OpenAI TTS detects language automatically from the text
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text,
            response_format="wav"
        )

        audio_bytes = response.content
        print(f"[TTS] Synthesized {len(audio_bytes)} bytes (OpenAI, {language})")
        return audio_bytes
    