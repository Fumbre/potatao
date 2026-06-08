from threading import Lock
from translation.transcriber import FasterWhisperTranscriber
from translation.translator import OllamaTranslator
from translation.tts import PiperTTS


class TranslatorProcesser:
    
    _instance = None
    _lock = Lock()
    
    def __init__(self,faster_whisper_model: str, ollama_model: str):
        self.transcriber = FasterWhisperTranscriber(model_size= faster_whisper_model)
        self.translator = OllamaTranslator(model=ollama_model)
        self.tts = PiperTTS()
    
    @classmethod
    def init(cls,faster_whisper_model:str,ollama_model:str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(faster_whisper_model,ollama_model)
        
        return cls._instance
    
    
    @classmethod
    def get_transcriber(cls)->FasterWhisperTranscriber:
        return cls._instance.transcriber 
    
    @classmethod
    def get_translator(cls)->OllamaTranslator:
        return cls.translator
    
    @classmethod
    def get_tts(cls)->PiperTTS:
        return cls._instance.tts