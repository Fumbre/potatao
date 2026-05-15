from enum import Enum

class FileType(Enum):
    WAV = ("wav","wav/audio")
    
    def __init__(self, ext: str, mime: str):
        self.ext = ext
        self.mime = mime