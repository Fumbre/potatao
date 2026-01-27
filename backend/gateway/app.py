from gateway.config.gateway_config import app,service_match
from nacos.nacos_life import nacos_client
import httpx
from fastapi import Request,Response
from exceptions.base_exception import BaseServiceException

@app.api_route("/{full_path}",methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def router(full_path:str, request:Request):
    path = "/" + full_path
    service_name = service_match(path=path)
    if service_name is None:
        raise BaseServiceException(code=502, msg="service not found")
    
    service_instance = await nacos_client.get_instance(service_name)

    target_path = f"http://{service_instance['ip']}:{service_instance['port']}{path}"

    async with httpx.AsyncClient(timeout=10) as client:
        req_method = request.method
        req_header = dict(request.headers)
        req_body = await request.body()

        res = await client.request(
            req_method,
            target_path,
            headers= req_header,
            content=req_body,
            params=dict(request.query_params)
        )
    return Response(
        status_code=res.status_code,
        content= res.content,
        headers= res.headers
    )
