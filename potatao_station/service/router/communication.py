import json
from typing import Dict

from fastapi import APIRouter,WebSocket

from common.aws3.s3 import S3Util
from common.encrptytion.aes.aes import AESUtil
from common.redis.redis import RedisClient
from request.pico_device_request import CommunicationData

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
    try:
        while True:
            msg = await ws.receive_text()

            aes_key = RedisClient.get(f"pico_data_key:{machine_id}")
            if not aes_key:
                break

            data: CommunicationData = AESUtil.decrypyt(str(aes_key), msg)

            session_id = RedisClient.get(f"s3_session_id:{machine_id}")
            if session_id:
                S3Util.upload_parts(session_id, data=data["data"])

            if data.get("is_end"):
                target_id = data.get("target_machine_id")
                await manager.disconnect(machine_id)
                if target_id:
                    await manager.disconnect(target_id)
                break

    except Exception as e:
        print(f"WebSocket error for {machine_id}: {e}")
    finally:
        await manager.disconnect(machine_id)

    