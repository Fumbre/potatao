from typing import Dict
from asyncio import Queue
from fastapi import APIRouter,WebSocket
from starlette.concurrency import run_in_threadpool
import asyncio
from common.aws3.s3 import S3Util
from common.encrptytion.aes.aes import AESUtil
from common.redis.redis import RedisClient

router = APIRouter(prefix="/communication/pico",tags=["websocket"])

class WebsocketManager:

    def __init__(self):
        self.active_sessions:Dict[str,WebSocket] = {}


    async def connect(self,machine_id:str,ws:WebSocket):
        await ws.accept()
        self.active_sessions[machine_id] = ws


    async def disconnect(self,machine_id:str):
        if machine_id in self.active_sessions:
            del self.active_sessions[machine_id]

manager = WebsocketManager()


@router.websocket("/ws/{machine_id}")
async def websocket_endpoint(machine_id: str, ws: WebSocket):
    await manager.connect(machine_id, ws)
    audio_queue = Queue()
    session_id = RedisClient.get(f"s3_session_id:{machine_id}")
    aes_key = RedisClient.get(f"pico_data_key:{machine_id}")
    worker_task = asyncio.create_task(s3_upload_worker(session_id, audio_queue))
    try:
        while True:
            raw_data = await ws.receive_bytes()
            decrypted_data = AESUtil.decrypt_bytes(aes_key, raw_data)
            audio_data = decrypted_data[9:]
            await audio_queue.put(audio_data)
    except Exception as e:
        print(f"WebSocket error for {machine_id}: {e}")
    finally:
        await audio_queue.put(None)
        await worker_task
        await manager.disconnect(machine_id)



async def s3_upload_worker(session_id:str, queue:Queue):
    try:
        while True:
            data = await queue.get()
            if data is None:
                break
            try:
                await run_in_threadpool(S3Util.upload_parts, session_id, data=data)
            except Exception as e:
                print(f"!!! S3 Upload Error: {e}")
            queue.task_done()
    except Exception as e:
        print(f"!!! Worker Task Crashed: {e}")


    