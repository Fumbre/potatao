from enum import Enum
from typing import Optional

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from pyfilters import CountRedisBloomFilter as SyncBloom
from pyfilters.asyncio import CountRedisBloomFilter as AsyncBloom


# =====================
# Time Unit
# =====================

class TimeUnit(Enum):
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"


# =====================
# Redis Client
# =====================

class RedisClient:

    def __init__(self, config: dict):
        self._init_client(config)


    # ---------------------
    # Init
    # ---------------------

    def _init_client(self, config: dict):

        redis_conf = config["redis"]

        host = redis_conf["ip"]
        port = redis_conf["port"]
        db = redis_conf.get("db", 0)
        password = redis_conf.get("password")

        # Sync client
        self.sync: SyncRedis = SyncRedis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

        # Async client
        self.async_: AsyncRedis = AsyncRedis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )


    # ---------------------
    # Refresh (Nacos Update)
    # ---------------------

    async def refresh(self, config: dict):

        try:
            if self.sync:
                self.sync.close()
        except:
            pass

        try:
            if self.async_:
                await self.async_.close()
        except:
            pass

        self._init_client(config)


    # =====================
    # Basic KV
    # =====================

    def _to_seconds(
        self,
        expire: Optional[int],
        unit: TimeUnit
    ) -> Optional[int]:

        if expire is None:
            return None

        if unit == TimeUnit.SECOND:
            return expire

        if unit == TimeUnit.MINUTE:
            return expire * 60

        if unit == TimeUnit.HOUR:
            return expire * 3600

        if unit == TimeUnit.DAY:
            return expire * 86400

        raise ValueError(f"Unsupported TimeUnit: {unit}")


    # -------- Sync --------

    def set(
        self,
        key: str,
        value,
        expire: Optional[int] = None,
        unit: TimeUnit = TimeUnit.SECOND
    ):

        ttl = self._to_seconds(expire, unit)

        return self.sync.set(
            name=key,
            value=value,
            ex=ttl
        )


    def get(self, key: str):

        return self.sync.get(key)


    def delete(self, key: str) -> int:

        return self.sync.delete(key)


    # -------- Async --------

    async def aset(
        self,
        key: str,
        value,
        expire: Optional[int] = None,
        unit: TimeUnit = TimeUnit.SECOND
    ):

        ttl = self._to_seconds(expire, unit)

        return await self.async_.set(
            name=key,
            value=value,
            ex=ttl
        )


    async def aget(self, key: str):

        return await self.async_.get(key)


    async def adelete(self, key: str) -> int:

        return await self.async_.delete(key)


    # =====================
    # Bloom Filter
    # =====================

    def _get_sync_bloom(
        self,
        key: str,
        capacity: int = 1_000_000,
        error_rate: float = 0.001
    ) -> SyncBloom:

        return SyncBloom(
            redis=self.sync,
            key=key,
            capacity=capacity,
            error_rate=error_rate
        )


    def _get_async_bloom(
        self,
        key: str,
        capacity: int = 1_000_000,
        error_rate: float = 0.001
    ) -> AsyncBloom:

        return AsyncBloom(
            redis=self.async_,
            key=key,
            capacity=capacity,
            error_rate=error_rate
        )


    # -------- Sync --------

    def bloom_exists(self, name: str, value: str) -> bool:

        bf = self._get_sync_bloom(name)

        return value in bf


    def bloom_add(self, name: str, value: str):

        bf = self._get_sync_bloom(name)

        bf.add(value)


    def bloom_remove(self, name: str, value: str):

        bf = self._get_sync_bloom(name)

        bf.remove(value)


    # -------- Async --------

    async def abloom_exists(self, name: str, value: str) -> bool:

        bf = self._get_async_bloom(name)

        return value in bf


    async def abloom_add(self, name: str, value: str):

        bf = self._get_async_bloom(name)

        await bf.add(value)


    async def abloom_remove(self, name: str, value: str):

        bf = self._get_async_bloom(name)

        await bf.remove(value)
