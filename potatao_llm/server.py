from fastapi import FastAPI
from config.lifespan import lifespan
from controller.communication import router as communicationRouter
from controller.data_transmission import router as websocketRouter
# Import the server that will run the FastAPI application
import uvicorn
 
# Create FastAPI
app = FastAPI(lifespan=lifespan)
# include router
app.include_router(communicationRouter)
app.include_router(websocketRouter)
 
if __name__ == "__main__":
    # Run with: python server.py
    # Or: uvicorn server:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8001)