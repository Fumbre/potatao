from nacos.nacos_life import lifespan,service_config_from_nacos
from fastapi import FastAPI
from exceptions.register import register_global_exception

app = FastAPI(lifespan=lambda app: lifespan(app, "gateway"))

register_global_exception(app=app)