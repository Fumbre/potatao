from redis.client import Redis
from redis.connection import ConnectionPool
from threading import Lock
from typing import Any,Optional

class RedisClient:
    _client:Redis = None
    _lock = Lock()
    
    @classmethod
    def init(cls,ip:str,port:int,password:str,db:int,max_connection:int):
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                   redis_url = f"redis://:{password}@{ip}:{port}/{db}"
                   connection_pool = ConnectionPool.from_url(
                       url=redis_url,
                       max_connections = max_connection,
                       decode_responses = True
                   )
                   cls._client = Redis(connection_pool=connection_pool)
        return cls._client
    
    
    @classmethod
    def set(cls,key:str,value:Any,ex:Optional[int] = None)->bool:
        return bool(cls._client.set(key=key,value=value,ex=ex))
    
    @classmethod
    def get(cls,key:str)->Any:
        return cls._client.get(name=key)
    
    @classmethod
    def delete(cls,*key:str)->int:
        return cls._client.delete(names = key)