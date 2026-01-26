from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .base_exception import BaseServiceException

async def base_exception_handler(request:Request, exception: BaseServiceException):
    return JSONResponse(
        status_code=200,
        content={
            "code" : exception.code,
            "message": exception.msg,
            "path": request.url.path
        }
    )

async def base_http_exception_handler(request:Request,exception: HTTPException):
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "code" : exception.status_code,
            "message": exception.detail,
            "path": request.url.path
        }
    )




