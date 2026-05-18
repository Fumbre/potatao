import threading
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import serialization, hashes
import json
import base64

class RSAUtil:
    
    _instance = None
    _lock = threading.Lock()
    
    
    @classmethod
    def init(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
        return cls._instance
    
    
    @classmethod
    def create_keypair(cls)->dict:
        private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
        public_key = private_key.public_key()
        private_key_str = private_key.private_bytes(encoding=serialization.Encoding.PEM,format=serialization.PrivateFormat.PKCS8,encryption_algorithm=serialization.NoEncryption).decode("utf-8")
        public_key_str = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo()).decode("utf-8")
        result = {}
        result["public_key"] = public_key_str
        result["private_key"] = private_key_str
        return result
    
    @classmethod
    def encrpyt(cls,payload:dict,public_key_str:str)->str:
        public_key = serialization.load_pem_public_key(public_key_str.encode("utf-8"))
        message = json.dumps(payload).encode("utf-8")
        encrpyted_text = public_key.encrypt(message,padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
        return base64.b64encode(encrpyted_text).decode("utf-8")
    
    
    @classmethod
    def decrpyt(cls,encrpyted_text:str,private_key_str:str)->dict:
        private_key = serialization.load_pem_private_key(private_key_str.encode("utf-8"),password=None)
        encrpyted_data = base64.b64decode(encrpyted_text)
        plaint_text = private_key.decrypt(
            encrpyted_data,
            padding=padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return json.loads(plaint_text.decode("utf-8"))