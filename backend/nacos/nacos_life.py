import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from nacos.nacos_client import Nacosclient
from utils.config_load import load_local_config

service_config = {}
service_config_from_nacos = {}

@asynccontextmanager
async def lifespan(app:FastAPI,service_name:str):
    global service_config,service_config_from_nacos
    ## get local application yaml 
    nacosConfig =  load_local_config(service_name)
    ## put service into Nacos
    nacos_client = Nacosclient(nacosConfig)
    await nacos_client.register_service()
    # intialize service basic information 
    service_config["service_name"] = nacosConfig["app"]["name"]
    service_config["ip"] = nacosConfig["server"]["host"]
    service_config["port"] = nacosConfig["server"]["port"]
    # get application configuration information from Nacos
    init_conf = await nacos_client.get_config()
    service_config_from_nacos.update(init_conf)
    #start 
    asyncio.create_task(nacos_client.listen_config(listen_change))
    print("Gateway application started")
    yield 
    print("Gateway application closed")


async def listen_change(new_config:dict):
    global service_config_from_nacos
    service_config_from_nacos.clear()
    service_config_from_nacos.update(new_config)
    print("Nacos config updated:", service_config_from_nacos)