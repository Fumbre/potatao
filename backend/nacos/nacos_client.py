import httpx
from typing import Optional, Callable
import yaml
import asyncio
import hashlib
from exceptions.base_exception import BaseServiceException

class Nacosclient:

    def __init__(self, config: dict):
        nacos = config["nacos"]
        self.service_name = config["app"]["name"]
        self.server_ip = nacos["server_ip"]
        self.server_port = nacos["server_port"]
        self.namespace = nacos["namespace"]
        self.group = nacos["group"]
        self.data_id = nacos["data_id"]
        self.ephemeral = nacos["ephemeral"]

        auth_conf = nacos.get("auth", {})
        self.auth_enabled: bool = auth_conf.get("enabled", False)
        self.username: Optional[str] = auth_conf.get("username")
        self.password: Optional[str] = auth_conf.get("password")

        self._keep_alive_task: Optional[asyncio.Task] = None

    async def register_service(self, service_config: dict) -> None:
        auth = (self.username, self.password) if self.auth_enabled and self.username and self.password else None
        async with httpx.AsyncClient(auth=auth, timeout=10) as client:
            resp = await client.post(
                f"http://{self.server_ip}:{self.server_port}/nacos/v2/ns/instance",
                params={
                    "serviceName": self.service_name,
                    "ip": service_config["ip"],
                    "port": service_config["port"],
                    "namespaceId": self.namespace,
                    "weight": 1,
                    "healthy": True,
                    "ephemeral": self.ephemeral
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()

            if self.ephemeral:
                self._start_keep_alive(service_config)

    def _start_keep_alive(self, service_config: dict, interval: int = 5):
        if self._keep_alive_task is None:
            self._keep_alive_task = asyncio.create_task(
                self._keep_alive_loop(service_config, interval)
            )

    async def _keep_alive_loop(self, service_config: dict, interval: int = 5):
        auth = (self.username, self.password) if self.auth_enabled else None
        async with httpx.AsyncClient(auth=auth, timeout=10) as client:
            try:
                while True:
                    try:
                        resp = await client.put(
                            f"http://{self.server_ip}:{self.server_port}/nacos/v1/ns/instance/beat",
                            params={
                                "serviceName": self.service_name,
                                "ip": service_config["ip"],
                                "port": service_config["port"],
                                "namespaceId": self.namespace,
                                "healthy": True
                            },
                            headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
                        resp.raise_for_status()
                    except Exception as e:
                        print(f"[Nacos] Heartbeat failed, retrying register: {e}")
                        await self.register_service(service_config)
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                print("[Nacos] Heartbeat stopped")

    async def get_config(self) -> dict:
        auth = (self.username, self.password) if self.auth_enabled and self.username and self.password else None
        async with httpx.AsyncClient(auth=auth, timeout=10) as client:
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

    async def get_instance(self, service_name: str) -> dict:
        auth = (self.username, self.password) if self.auth_enabled and self.username and self.password else None
        try:
            async with httpx.AsyncClient(auth=auth, timeout=10) as client:
                resp = await client.get(
                    f"http://{self.server_ip}:{self.server_port}/nacos/v2/ns/instance/list",
                    params={
                        "serviceName": service_name,
                        "namespaceId": self.namespace
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                if not data.get("hosts"):
                    raise BaseServiceException(code=503, msg=f"No healthy instances for {service_name}")
                host = data["hosts"][0]
                return {"ip": host["ip"], "port": host["port"]}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise BaseServiceException(code=404, msg=f"{service_name} not found in Nacos!")
        except httpx.RequestError as e:
            raise BaseServiceException(code=500, msg=f"Request to Nacos failed: {e}")

    async def deregister_service(self, service_config: dict) -> None:
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
            self._keep_alive_task = None

        auth = (self.username, self.password) if self.auth_enabled and self.username and self.password else None
        async with httpx.AsyncClient(auth=auth, timeout=10) as client:
            try:
                resp = await client.delete(
                    f"http://{self.server_ip}:{self.server_port}/nacos/v2/ns/instance",
                    params={
                        "serviceName": self.service_name,
                        "ip": service_config["ip"],
                        "port": service_config["port"],
                        "namespaceId": self.namespace,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                resp.raise_for_status()
                print(f"Service {self.service_name} at {service_config['ip']}:{service_config['port']} deregistered successfully")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    print(f"Service {self.service_name} not found in Nacos, already deregistered?")
                else:
                    print(f"Failed to deregister service {self.service_name}: {e}")
            except httpx.RequestError as e:
                print(f"Request to Nacos failed during deregister: {e}")
