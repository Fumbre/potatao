from libs.ws.ws import AsyncWebsocketClient
from libs.conf.env import load_env
from libs.encrpytion.encryption import encrypt_data,decrypt_data,get_machine_id
import requests
import uasyncio
from libs.managers.queue import SimpleQueue

client = AsyncWebsocketClient()
config = load_env()


async def ws_connect():
   machine_id = get_machine_id()
   ws_url = f"ws://{config.get('ZERO_IP')}:{config.get('ZERO_PORT')}{config.get('PICO_WS_API')}/{machine_id}"
   try:
       if await uasyncio.wait_for(client.handshake(uri=ws_url), timeout=5):
           await client.open() 
           print("websocket connected successfully!")
           return True
   except Exception as e:
       print("Handshake failed:", e)
   return False
   
       


async def ws_send(queue:SimpleQueue):  
    while True:
        data = await queue.get()
        try:
            if client and client._open:
                await client.send(data)
                await uasyncio.sleep(0)
        except Exception as e:
            print("ws send error:",e)
        finally:
            queue.task_done()


async def ws_receive():
    if client and client._open:
        data = await client.recv()
        return data
    return b""    
        

async def disconnect():
    machine_id = get_machine_id()
    if client and client._open:
        await client.close()        
    try:
        disconnect_url = f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('pico_WS_DISCONNECT_API','')}/{machine_id}"
        requests.get(url=disconnect_url)
    except:
        pass