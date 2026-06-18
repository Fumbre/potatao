# ws/ws_manager.py
from typing import Dict
from starlette.websockets import WebSocket


class WebsocketManager:

    def __init__(self):
        self.active_sessions: Dict[str, WebSocket] = {}

    async def connect(self, machine_id: str, ws: WebSocket):
        await ws.accept()
        self.active_sessions[machine_id] = ws
        print(f"[Manager] CONNECTED: {machine_id}, total={len(self.active_sessions)}, keys={list(self.active_sessions.keys())}")

    async def disconnect(self, machine_id: str):
        if machine_id in self.active_sessions:
            del self.active_sessions[machine_id]
            print(f"[Manager] DISCONNECTED: {machine_id}, remaining={list(self.active_sessions.keys())}")