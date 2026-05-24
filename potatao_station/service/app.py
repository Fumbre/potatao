from fastapi import FastAPI

from common.exception.exception_handler import register_exception_handler
from config.lifespan import lifespan
from service.router.pico_device import router as pico_device_router

app = FastAPI(lifespan=lifespan)
register_exception_handler(app)

app.include_router(pico_device_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service.app:app", host="0.0.0.0", port=8000, reload=True)