from fastapi import FastAPI,HTTPException
from .base_exception import BaseServiceException
from .exception_handler import base_exception_handler,base_http_exception_handler

def register_global_exception(app:FastAPI):
    app.add_exception_handler(BaseServiceException,base_exception_handler)
    app.add_exception_handler(HTTPException, base_http_exception_handler)