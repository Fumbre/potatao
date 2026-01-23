import httpx
from typing import Optional,Callable
import yaml
import asyncio
import hashlib

class Nacosclient:

    def __init__(self,config:dict):
        nacos = config["nacos"]
        self.service_name = config["app"]["name"]
        self.server_ip = nacos["server_ip"]
        self.server_port = nacos["server_port"]
        self.namespace = nacos["namespace"]
        self.group = nacos["group"]
        self.data_id = nacos["data_id"]

        auth_conf = nacos.get("auth", {})
        self.auth_enabled: bool = auth_conf.get("enabled", False)
        self.username: Optional[str] = auth_conf.get("username")
        self.password: Optional[str] = auth_conf.get("password")


    async def register_service(self) -> dict :
        auth = (self.username, self.password) if self.auth_enabled and self.username and self.password else None
        async with httpx.AsyncClient(auth=auth, timeout=10) as client:
            resp = await client.post(
                f"http://{self.server_ip}:{self.server_port}/nacos/v1/ns/instance",
                params={
                    "serviceName": self.service_name,
                    "ip": self.server_ip,
                    "port": self.server_port,
                    "namespaceId": self.namespace,
                    "weight": 1,
                    "healthy": True,
                    "ephemeral": True
                }
            )
            resp.raise_for_status()

    async def get_config(self) -> dict:
        auth = (self.username, self.password) if self.auth_enabled and self.username and self.password else None
        async with httpx.AsyncClient(auth=auth,timeout=10) as client:
            resp = await client.get(
                f"http://{self.server_ip}:{self.server_port}/nacos/v1/cs/configs",
                params={
                    "tenant": self.namespace,
                    "group": self.group,
                    "dataId": self.data_id
                }
            )
            resp.raise_for_status()
            return yaml.safe_load(resp.text)
    
        
    async def listen_config(self, callback: Callable[[dict], None], interval: int = 5):
        current_md5 = None
        while True:
            try:
                config = await self.get_config()
                md5 = hashlib.md5(yaml.dump(config).encode("utf-8")).hexdigest()
                if md5 != current_md5:
                    current_md5 = md5
                    await callback(config)
            except Exception as e:
                print(f"get nacos configuration information failed: {e}")
            await asyncio.sleep(interval)               