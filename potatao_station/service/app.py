from fastapi import FastAPI

from config.lifespan import lifespan

app = FastAPI(lifespan=lifespan)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service.app:app", host="0.0.0.0", port=8000, reload=True)