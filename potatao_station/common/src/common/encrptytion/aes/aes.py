import json
import os
import secrets
import threading
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

class AESUtil:
    
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
    def encrypt(cls,key:str,data:dict)->str:
        key_bytes = bytes.fromhex(key)
        if len(key_bytes) not in [16,24,32]:
            raise ValueError("the length of AES key must be 16, 24 and 32!")
        raw_bytes = json.dumps(data).encode('utf-8')
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(raw_bytes) + padder.finalize()

        cipher = Cipher(algorithm=algorithms.AES(key=key_bytes), mode=modes.CBC(iv))
        encryptor = cipher.encryptor()
        cipher_text = encryptor.update(padded_data) + encryptor.finalize()
        return iv.hex() + cipher_text.hex()
    
    
    @classmethod
    def decrypyt(cls,key:str,data:str)->dict:
        key_bytes = bytes.fromhex(key)
        if len(key_bytes) not in [16, 24, 32]:
            raise ValueError("the length of AES key must be 16, 24 and 32!")
        encrypted_data = bytes.fromhex(data)
        iv = encrypted_data[:16]
        cipher_text = encrypted_data[16:]
        cipher = Cipher(algorithm=algorithms.AES(key_bytes), mode=modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(cipher_text) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        decrypted_bytes = unpadder.update(padded_data) + unpadder.finalize()
        return json.loads(decrypted_bytes.decode('utf-8'))