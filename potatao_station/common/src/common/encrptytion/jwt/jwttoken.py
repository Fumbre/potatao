import jwt
import datetime
import threading

class TokenUitl:
    
    _instance = None
    _secrect = None
    _algorithm = "HS256"
    _lock = threading.Lock()
    
    
    @classmethod
    def init(cls,secrect_key:str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._secrect = secrect_key
        return cls._instance
    
    
    @classmethod
    def generate_token(cls,payload:dict)->str:
        payload["timestamp"] = datetime.datetime.now().timestamp()
        return jwt.encode(payload=payload,key=cls._secrect,algorithm=cls._algorithm)
    
    
    @classmethod
    def decode_token(cls,token:str)->dict:
        return jwt.decode(jwt=token,key=cls._secrect,algorithms=[cls._algorithm])