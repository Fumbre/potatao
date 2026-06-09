from threading import Lock
from typing import Any, Optional, Dict

from httpx import AsyncClient


class HttpUtil:

    _instance:AsyncClient = None
    _lock = Lock()

    def __init__(self, base_url: str):
        self.client = AsyncClient(base_url=base_url)

    @classmethod
    def init(cls,base_url:str):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(base_url)

        return cls._instance

    @classmethod
    async def get(cls, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 5) -> Any:
        response = await cls._instance.client.get(url, timeout=timeout, params=params)
        response.raise_for_status()
        return response.json()

    @classmethod
    async def post(cls,url:str,data:dict,timeout:int=5)->Any:
        response = await cls._instance.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()

    @classmethod
    async def close(cls):
        if cls._instance is not None:
           await cls._instance.aclose()