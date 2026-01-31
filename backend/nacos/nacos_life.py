from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from nacos.nacos_client import Nacosclient
from utils.config_load import load_local_config,get_local_ip
from utils.redisUtils import RedisClient
from database.database_config import init_db,SessionLocal
from utils.snowflake_id_util  import init_snowflake
from nacos.nacos_event import config_ready_event


service_config = {}
service_config_from_nacos = {}
nacos_client : Nacosclient | None = None
redis_client : RedisClient | None = None

@asynccontextmanager
async def lifespan(app:FastAPI,service_name:str):
    global service_config,service_config_from_nacos,nacos_client
    ## get local application yaml 
    nacosConfig =  load_local_config(service_name)
    # intialize service basic information 
    service_config["service_name"] = nacosConfig["app"]["name"]
    service_config["ip"] = get_local_ip()
    service_config["port"] = nacosConfig["server"]["port"]
    ## put service into Nacos
    nacos_client = Nacosclient(nacosConfig)
    await nacos_client.register_service(service_config)
    app.state.nacos_client = nacos_client
    # get application configuration information from Nacos
    init_conf = await nacos_client.get_config()
    service_config_from_nacos.update(init_conf)
    # init redis information
    if service_config_from_nacos.get("redis") is not None:
        global redis_client
        redis_client = RedisClient(service_config_from_nacos)
        app.state.redis_client = redis_client
    #init database
    if service_config_from_nacos.get("database") is not None:
        init_db(service_config_from_nacos["database"])            
    asyncio.create_task(nacos_client.listen_config(listen_change))
    #init snowflake Id
    if service_config_from_nacos.get("snowflake") is not None:
        init_snowflake(service_config_from_nacos)

    config_ready_event.set()

    print(f"{service_name} application started")
    yield 
    if SessionLocal:
        SessionLocal().bind.dispose()
    await nacos_client.deregister_service(service_config)    
    print(f"{service_name} application closed")


async def listen_change(new_config:dict):
    global service_config_from_nacos
    service_config_from_nacos.clear()
    service_config_from_nacos.update(new_config)
    if service_config_from_nacos.get("redis") is not None:
        await redis_client.refresh(service_config_from_nacos)

    if service_config_from_nacos.get("database") is not None:
        if SessionLocal:
           init_db(service_config_from_nacos["database"])    
    print("Nacos config updated:", service_config_from_nacos)

def service_match(path:str)->str | None:
    #get service information from nacos
    service_config = service_config_from_nacos["route"]
    for service in service_config:
        route_path = str(service["path"])
        if route_path.endswith("*"):
            prefix = route_path[:-1]
            if path.startswith(prefix):
                return service["service"]
            if route_path == path:
                return service["service"]
    return None       
