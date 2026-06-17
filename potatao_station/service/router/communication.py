import json
from asyncio import Queue

from fastapi import APIRouter, WebSocket
from starlette.concurrency import run_in_threadpool
import asyncio
from common.aws3.s3 import S3Util
from common.encrptytion.aes.aes import AESUtil
from common.redis.redis import RedisClient
import websockets

from service.zero_service import construct
from ws.ws_manager import WebsocketManager

router = APIRouter(prefix="/communication/pico",tags=["websocket"])


manager = WebsocketManager()


@router.websocket("/ws/{machine_id}")
async def websocket_endpoint(machine_id: str, ws: WebSocket):
    await manager.connect(machine_id, ws)
    audio_queue = Queue()
    translation_queue = Queue()
    translated_queue = Queue()
    session_id = RedisClient.get(f"s3_session_id:{machine_id}")
    aes_key = RedisClient.get(f"pico_data_key:{machine_id}")
    worker_task = asyncio.create_task(s3_upload_worker(session_id, audio_queue))
    translation_task = asyncio.create_task(translation_worker(machine_id, translation_queue, translated_queue,target_id=machine_id))
    send_task = asyncio.create_task(translated_sender(machine_id,manager,aes_key,translated_queue))
    try:
        while True:
            raw_data = await ws.receive_bytes()
            decrypted_data = AESUtil.decrypt_bytes(aes_key, raw_data)
            audio_data = decrypted_data[9:]
            await audio_queue.put(audio_data)
            await translation_queue.put(decrypted_data)
    except Exception as e:
        print(f"WebSocket error for {machine_id}: {e}")
    finally:
        await audio_queue.put(None)
        await translation_queue.put(None)
        await translated_queue.put(None)
        await asyncio.gather(worker_task, translation_task, send_task,return_exceptions=True)
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


async def translation_worker(machine_id: str, queue: Queue, translation_queue: Queue, target_id: str):
    llm_websocket_url = f"ws://127.0.0.1:8001/communicating/audio/{target_id}"
    send_key = RedisClient.get(f"llm_data_key:{machine_id}")
    print(f"[Station] llm_key from redis={send_key}")
    recv_key = RedisClient.get(f"aes_key:{target_id}")
    session_id_list = json.loads(RedisClient.get(f"user_translated_session:{machine_id}"))
    try:
        async with websockets.connect(llm_websocket_url) as ws:
            recv_task = asyncio.create_task(receiver(ws=ws,session_id_list=session_id_list,translation_queue=translation_queue,recv_key=recv_key))

            while True:
                data = await queue.get()
                if data is None:
                    break
                encrypted_data = construct(data=data, websocket_manager=manager, machine_id=machine_id)
                await ws.send(encrypted_data)
                queue.task_done()

            recv_task.cancel()
    except Exception as e:
        print(f"!!! Translation Worker Crashed: {e}")


async def translated_sender(machine_id:str,manager:WebsocketManager,queue:Queue):
    languages:dict = json.loads(RedisClient.get("user_language"))
    while True:
        data = await queue.get()
        if data is None:
            break
        binary_code, audio_data = data
        sessions =  manager.active_sessions
        for machine in sessions:
            if machine != machine_id:
                if languages[machine]["binary_code"] == binary_code:
                    aes_key = json.loads(RedisClient.get(f"receive_aes_key:{machine}"))
                    encrypted_data = AESUtil.encrypt_bytes(aes_key, audio_data)
                    await sessions[machine].send_bytes(encrypted_data)
        queue.task_done()


async def receiver(ws,session_id_list:dict,recv_key:str,translation_queue:Queue):
    async for message in ws:
        final_data = AESUtil.decrypt_bytes(recv_key, message)
        print(f"[Receiver] final_data len={len(final_data)}")
        offset = 0
        while offset < len(final_data):
            binary_code = final_data[offset]
            offset = offset + 1
            audio_len = int.from_bytes(final_data[offset:offset + 4], "big")
            offset += 4
            audio_data = final_data[offset:offset + audio_len]
            offset += audio_len
            session_id = session_id_list[str(binary_code)]
            if session_id:
                await run_in_threadpool(S3Util.upload_parts, session_id = session_id, data=audio_data)
            await translation_queue.put((binary_code, audio_data))