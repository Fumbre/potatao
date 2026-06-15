from typing import Dict

from starlette.websockets import WebSocket


class WebsocketManager:

    def __init__(self):
        self.active_sessions:Dict[str,WebSocket] = {}


    async def connect(self,machine_id:str,ws:WebSocket):
        await ws.accept()
        self.active_sessions[machine_id] = ws


    async def disconnect(self,machine_id:str):
        if machine_id in self.active_sessions:
            del self.active_sessions[machine_id]