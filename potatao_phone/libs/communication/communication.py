import ws
from libs.conf.env import load_env
from libs.encrpytion.encryption import encrypt_data,decrypt_data,get_machine_id

client = ws.AsyncWebsocketClient()
config = load_env()
is_sending = False

async def ws_connect():
   machine_id = get_machine_id()
   ws_url = f"ws://{config.get('ZERO_IP')}:{config.get('ZERO_PORT')}{config.get('PICO_WS_API')}/{machine_id}"
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