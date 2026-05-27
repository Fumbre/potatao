import ws
from libs.conf.env import load_env
import uasyncio
from libs.encrpytion.encryption import encrypt_data,decrypt_data

client = ws.AsyncWebsocketClient()
config = load_env()
is_sending = False

async def ws_connect():
   ws_url = f"ws://{config.get('ZERO_IP')}:{config.get('ZERO_PORT')}/api/v1/ws/audio"
   if await client.handshake(uri=ws_url):
       await client.open() 
       print("websocket connected successfully!")
       


async def ws_send(data:dict):
    global is_sending
    if is_sending:
        return   
    is_sending = True   
    try:
        if client and client._open:
           text =  encrypt_data(data)
           await client.send(text)
    finally:
        is_sending = False


# async def ws_receive()->dict:
#             ...