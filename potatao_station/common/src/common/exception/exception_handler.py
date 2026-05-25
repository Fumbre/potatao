from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse

from common.exception.base import BusinessException
from common.response.base_response import BaseResponse


def register_exception_handler(app: FastAPI):

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException)->JSONResponse:
        res_data = BaseResponse.response(code=exc.code,message=exc.message)
        return JSONResponse(
            status_code=exc.code,
            content=res_data.dict()
        )
