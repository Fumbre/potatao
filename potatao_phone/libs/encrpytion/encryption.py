import requests
from requests import Response
import machine
import ubinascii
import x25519
import hmac
import os
import cryptolib
from libs.conf.env import load_env
import ujson
import jwt

CONVERSATION_AES_KEY = None

def register():
    ## configuration information from env
    config = load_env()
    ## get pico machine id
    machine_id = get_machine_id()
    data = {"machine_id":machine_id}
    url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('PICO_REGISTER_API','')}"
    response:Response = requests.post(url=url,data=ujson.dumps(data))
    response.close()
        
    
def shake_hands():
    global CONVERSATION_AES_KEY
    ## configuration information from env
    config = load_env()
    ## get pico machine id
    machine_id = get_machine_id()
    ## check whether pico has already registered
    url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('PICO_REGISTERATION_CHECK_API','')}/{machine_id}"
    response:Response =  requests.get(url=url)
    if not bool(response.json()["data"]):
        ## TODO: remind user register device firstly
        return
    response.close()
    ## generare keypair by X25519
    private_key,public_key = keypairs()
    #get secret key
    secret_key = config.get("SECRET_KEY","")
    payload = {
        "machine_id":machine_id,
        "pico_public_key":bytes_to_hex(public_key)
    }
    token = jwt.create_token(payload=ujson.dumps(payload),secret_key=secret_key)
    data = {
        "data":token
    }
    # get zero public key
    key_url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('PICO_AUTHORIZATION_API','')}"
    res:Response = requests.post(url=key_url,data=ujson.dumps(data))
    res_data = res.json()
    zero_public_key = res_data["data"]
    res.close()
    #generate aes key
    CONVERSATION_AES_KEY = generate_aes_key(pico_private_key=private_key,zero_public_key=zero_public_key,secret_key=secret_key)

def get_machine_id()->str:
    return ubinascii.hexlify(machine.unique_id()).decode("utf-8")

def keypairs()->tuple:
    private_key = os.urandom(32)
    public_key = x25519.calculate(private_key,x25519.BASE_POINT)
    return private_key,public_key

def bytes_to_hex(b):
    return "".join("{:02x}".format(x) for x in b)


def generate_aes_key(pico_private_key:bytes,zero_public_key:str,secret_key:str)->str:
    zero_public_key_bytes = ubinascii.unhexlify(zero_public_key)
    raw_result = x25519.calculate(pico_private_key,zero_public_key_bytes)
    salt = b"\x00" * 32
    prk = hmac.new(key=salt,msg=raw_result,digestmod="sha256").digest()
    info = secret_key.encode("utf-8") + b"\x01"
    okm = hmac.new(key=prk,msg=info,digestmod="sha256").digest()
    aes_bytes = okm[:16]
    return bytes_to_hex(aes_bytes)


def encrypt_data(payload:dict)->str:
    global CONVERSATION_AES_KEY
    aes_key = ubinascii.unhexlify(CONVERSATION_AES_KEY)
    data_str = ujson.dumps(payload)
    data_binary = data_str.encode("utf-8")
    pad_len = 16 - (len(data_binary) % 16)
    final_data =  data_binary + bytes([pad_len] * pad_len)
    iv = os.urandom(16)
    aes_cipher = cryptolib.aes(aes_key,2,iv)
    cipher_text = aes_cipher.encrypt(final_data)
    data_package = iv + cipher_text
    hex_str = ubinascii.hexlify(data_package).decode("utf-8")
    return hex_str


def decrypt_data(data:str)->dict:
    global CONVERSATION_AES_KEY
    if CONVERSATION_AES_KEY is None:
        return {}
    if not data:
        return {}
    aes_key = ubinascii.unhexlify(CONVERSATION_AES_KEY)
    raw_data_package = ubinascii.unhexlify(data)
    iv = raw_data_package[:16]
    cipher_text = raw_data_package[16:]
    aes_cipher = cryptolib.aes(aes_key, 2, iv)
    decryted_pad = aes_cipher.decrypt(cipher_text)
    pad_len = decryted_pad[-1]
    raw_data_binary = decryted_pad[:-pad_len]
    return ujson.loads(raw_data_binary.decode("utf-8"))