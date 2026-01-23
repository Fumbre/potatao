from nacos.nacos_life import lifespan
from fastapi import FastAPI

app = FastAPI(lifespan=lambda app: lifespan(app, "gateway"))