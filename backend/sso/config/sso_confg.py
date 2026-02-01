from nacos.nacos_life import lifespan,service_config,service_match,redis_client
from fastapi import FastAPI
from exceptions.register import register_global_exception

app = FastAPI(lifespan=lambda app: lifespan(app, "sso"))
register_global_exception(app=app)
