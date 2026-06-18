import requests
from requests import Response
import machine
import ubinascii
import uhashlib
import x25519
import os
import cryptolib
from libs.conf.env import load_env
import ujson
import jwt

CONVERSATION_AES_KEY = None
RECEIVE_AES_KEY = None

def register():
    ## configuration information from env
    config = load_env()
    secret_key = config.get("SECRET_KEY")
    ## get pico machine id
    machine_id = get_machine_id()
    data = {"machine_id":machine_id}
    token = jwt.create_token(ujson.dumps(data),secret_key)
    real_data = {
        "data":token
    }
    url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('PICO_REGISTER_API','')}"
    response:Response = requests.post(url=url,json=real_data)
    response.close()
        
    
def shake_hands(prefered_language:str):
    global CONVERSATION_AES_KEY
    ## configuration information from env
    config = load_env()
    ## get pico machine id
    machine_id = get_machine_id()
    ## check whether pico has already registered
    url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('PICO_REGISTERATION_CHECK_API','')}/{machine_id}"
    response:Response =  requests.get(url=url)
    if not bool(response.json()["data"]):
        response.close()
        return
    response.close()
    ## generare keypair by X25519
    private_key,public_key = x25519.generate_keypair()
    #get secret key
    secret_key = config.get("SECRET_KEY","")
    payload = {
        "machine_id":machine_id,
        "pico_public_key":bytes_to_hex(public_key),
        "prefered_language":prefered_language
    }
    token = jwt.create_token(ujson.dumps(payload),secret_key)
    data = {
        "data":token
    }
    # get zero public key
    key_url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('PICO_AUTHORIZATION_API','')}"
    res:Response = requests.post(url=key_url,json=data)
    res_data = res.json()
    zero_public_key = res_data["data"]
    res.close()
    #generate aes key
    CONVERSATION_AES_KEY = generate_aes_key(private_key,zero_public_key=zero_public_key,secret_key=secret_key)


def receive_hand_shake(prefered_language:str):
    global RECEIVE_AES_KEY
    ## configuration information from env
    config = load_env()
    ## get pico machine id
    machine_id = get_machine_id()
    private_key,public_key = x25519.generate_keypair()
    #get secret key
    secret_key = config.get("SECRET_KEY","")
    payload = {
        "machine_id":machine_id,
        "pico_public_key":bytes_to_hex(public_key),
        "prefered_language":prefered_language
    }
    token = jwt.create_token(ujson.dumps(payload),secret_key)
    data = {
        "data":token
    }
    # get zero public key
    key_url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('RECEIVE_HAND_SHAKE','')}"
    res:Response = requests.post(url=key_url,json=data)
    res_data = res.json()
    zero_public_key = res_data["data"]
    res.close()
    #generate aes key
    RECEIVE_AES_KEY = generate_aes_key(private_key,zero_public_key=zero_public_key,secret_key=secret_key)
    
    

def get_machine_id()->str:
    return ubinascii.hexlify(machine.unique_id()).decode("utf-8")



def bytes_to_hex(b):
    return "".join("{:02x}".format(x) for x in b)


def generate_aes_key(pico_private_key: bytes, zero_public_key: str, secret_key: str) -> str:
    zero_public_key_bytes = ubinascii.unhexlify(zero_public_key)
    raw_result = x25519.calculate(pico_private_key, zero_public_key_bytes)
    sha256 = uhashlib.sha256()
    sha256.update(raw_result)
    sha256.update(secret_key.encode("utf-8"))
    digest = sha256.digest()
    aes_bytes = digest[:16]
    return ubinascii.hexlify(aes_bytes).decode('utf-8')



def encrypt_data(payload:bytes,key:str)->bytes:
    if not key: return b''
    aes_key = ubinascii.unhexlify(key)
    pad_len = 16 - (len(payload) % 16)
    padded_data = payload + bytes([pad_len] * pad_len)
    
    iv = os.urandom(16)
    aes_cipher = cryptolib.aes(aes_key, 2, iv)
    cipher_text = aes_cipher.encrypt(padded_data)
    
    return iv + cipher_text


def decrypt_data(data: bytes,key:str) -> bytes:
    if key is None:
        return b''
    if not data:
        return b''
    aes_key = ubinascii.unhexlify(key)
    iv = data[:16]
    cipher_text = data[16:]
    aes_cipher = cryptolib.aes(aes_key, 2, iv)
    decrypted_pad = aes_cipher.decrypt(cipher_text)
    pad_len = decrypted_pad[-1]
    raw_data_binary = decrypted_pad[:-pad_len]
    return raw_data_binary


