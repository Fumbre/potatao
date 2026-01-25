from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis
from nacos.nacos_life import service_config_from_nacos

class RedisClient:

    def __init__(self):
        self._init_client()
        
    def _init_client(self):
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
    
        
    async def refresh(self):
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

        self._init_client()                       