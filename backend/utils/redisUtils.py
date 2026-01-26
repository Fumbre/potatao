from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis
from enum import Enum

class TimeUnit(Enum):
    SECOND = "s"
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"

class RedisClient:

    def __init__(self,service_config_from_nacos):
        self._init_client(service_config_from_nacos)
        
    def _init_client(self,service_config_from_nacos):
        host = service_config_from_nacos["redis"]["ip"]
        port = service_config_from_nacos["redis"]["port"]
        db = service_config_from_nacos["redis"]["db"]
        password = service_config_from_nacos["redis"]["password"]

        self.sync: SyncRedis = SyncRedis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

        self.async_: AsyncRedis = AsyncRedis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
    
        
    async def refresh(self,service_config_from_nacos):
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

        self._init_client(service_config_from_nacos)

     
    def _to_seconds(self, expire: int | None, unit: TimeUnit) -> int | None:
      if expire is None:
        return None

      if unit == TimeUnit.SECOND:
        return expire
      elif unit == TimeUnit.MINUTE:
        return expire * 60
      elif unit == TimeUnit.HOUR:
        return expire * 3600
      elif unit == TimeUnit.DAY:
        return expire * 86400

      raise ValueError(f"Unsupported TimeUnit: {unit}")
    

    def set(self, key:str, value, expire: int | None = None, unit: TimeUnit = TimeUnit.SECOND):
       timeValue = self._to_seconds(expire=expire,unit=unit)
       return self.sync.set(name = key,
                     value = value,
                     ex = timeValue)

    def get(self, key:str):
       return self.sync.get(key)

    def delete(self,key:str) -> int:
       return self.sync.delete(key)

    async def aset(self, key:str, value, expire: int | None = None, unit: TimeUnit = TimeUnit.SECOND):
       timeValue = self._to_seconds(expire=expire,unit=unit)
       return await self.async_.set(
          name = key,
          value = value,
          ex = timeValue
       )
    
    async def aget(self,key:str):
       return await self.async_.get(key)
    
    async def adelete(self, key:str) -> int:
       return await self.async_.delete(key)