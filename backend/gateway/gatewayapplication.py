from .config.gateway_config import app,service_match
from nacos.nacos_life import nacos_client
from utils.config_load import load_local_config
import httpx
from fastapi import Request,Response
from exceptions.base_exception import BaseServiceException
import random

@app.api_route("/{full_path}",methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def router(full_path:str, request:Request):
    path = "/" + full_path
    service_name = service_match(path=path)
    if service_name is None:
        raise BaseServiceException(code=502, msg="service not found")
    
    instance_list = await nacos_client.get_instance(service_name)
    if instance_list is None or len(instance_list) == 0 :
        raise BaseServiceException(code=502, msg="service not found")
    service_instance = random.choice(instance_list) if len(instance_list) > 1 else instance_list[0]

    target_path = f"http://{service_instance['ip']}:{service_instance['port']}{path}"

    req_header = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    async with httpx.AsyncClient() as client:
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




if __name__ == "__main__":
    import uvicorn
    config = load_local_config("gateway")
    uvicorn.run("gatewayapplication:app",host=config["server"]["host"],port=config["server"]["port"],reload=True)
