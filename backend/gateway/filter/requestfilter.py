from gateway.config.gateway_config import app,service_config_from_nacos
from starlette.middleware.base import BaseHTTPMiddleware
from utils.config_load import path_match
from ...utils.jwt_utils import verify_access_token
from ...nacos.nacos_life import redis_client
from ...exceptions.base_exception import AuthException


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
        if token and token.startswith("Bearer "):
            token = token[7:]

        if not token:
            raise AuthException(code=401,msg="Unauthorized !")
        information = verify_access_token(token)
        if information is None:
            raise AuthException(code=401,msg="Unauthorized !")
        userInfo = redis_client.get(f"user:{information['uuid']}")
        if userInfo is None:
            raise AuthException(code=401,msg="Unauthorized !")
        response = await call_next(request)
        return response


app.add_middleware(GatewayFilter)