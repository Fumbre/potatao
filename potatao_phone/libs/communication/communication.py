from libs.ws.ws import AsyncWebsocketClient
from libs.conf.env import load_env
from libs.encrpytion.encryption import encrypt_data,decrypt_data,get_machine_id
from libs.managers.state_manager import StateManager
import requests


client = AsyncWebsocketClient()
config = load_env()


async def ws_connect():
   machine_id = get_machine_id()
   ws_url = f"ws://{config.get('ZERO_IP')}:{config.get('ZERO_PORT')}{config.get('PICO_WS_API')}/{machine_id}"
   if await client.handshake(uri=ws_url):
       await client.open() 
       print("websocket connected successfully!")
       


async def ws_send(data:dict,state:StateManager):  
    try:
        if client and client._open:
           text =  encrypt_data(data)
           await client.send(text)
    finally:
        state.is_sending = False

async def disconnect():
    machine_id = get_machine_id()
    if client and client._open:
        await client.close()        
    disconnect_url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('pico_WS_DISCONNECT_API','')}/{machine_id}"
    requests.get(url=disconnect_url)