from gateway.config.gateway_config import app,service_config_from_nacos
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from utils.config_load import path_match

class GatewayFilter(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        path = request.url.path

        exclude = (
            service_config_from_nacos
            .get("filter",{})
            .get("exclude",[])
        )

        if path_match(path,exclude):
            return await call_next(request)
        
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse(
                status_code=401,
                content= {"msg":"Unauthorized"}
            )
        response = await call_next(request)
        return response