from nacos.nacos_life import lifespan,service_config,service_match,redis_client
from fastapi import FastAPI
from exceptions.register import register_global_exception
from sso.service.sso_service import selectUserList
from nacos.nacos_event import config_ready_event
import asyncio

_initialized_bloom = False

async def init_bloom():
    global _initialized_bloom
    if _initialized_bloom:
        return
    _initialized_bloom = True

    await config_ready_event.wait()

    #put user information into bloom filter
    if service_config["app"]["name"] == "sso":
    #get user information from DB
       user_list = selectUserList()
       if not user_list:
        for user in user_list:
            redis_client.abloom_add("bf:sso:username",user.username)
            redis_client.abloom_add("bf:sso:email",user.email)
            # redis_client.abloom_add("bf:sso:phone",user.phone)

app = FastAPI(lifespan=lambda app: lifespan(app, "sso"))

register_global_exception(app=app)

@app.on_event("startup")
async def startup_bloom():
    asyncio.create_task(init_bloom())