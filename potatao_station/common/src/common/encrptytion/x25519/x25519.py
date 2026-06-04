import hashlib
import threading
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

class X25519MUtil:
    
    _instance = None
    _lock = threading.Lock()
    _secret_key:str = None
    
    @classmethod
    def init(cls,secret_key:str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._secret_key = secret_key
        return cls._instance

    
    @classmethod
    def generate_keypair(cls)-> tuple[x25519.X25519PrivateKey,str]:
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        public_key_hex = public_key.public_bytes_raw().hex()
        return private_key,public_key_hex
    
    
    @classmethod
    def generate_data_encrypting_key(cls,private_key:x25519.X25519PrivateKey,pico_public_key:str)->str:
        pico_public_key_byte = bytes.fromhex(pico_public_key)
        pico_pub_key_obj = x25519.X25519PublicKey.from_public_bytes(pico_public_key_byte)
        raw_result = private_key.exchange(pico_pub_key_obj)
        info_context = cls._secret_key.encode("utf-8")
        sha256 = hashlib.sha256()
        sha256.update(raw_result)
        sha256.update(info_context)
        digest = sha256.digest()
        return digest[:16].hex()