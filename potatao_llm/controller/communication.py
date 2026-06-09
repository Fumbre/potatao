from fastapi.routing import APIRouter
from response.response import BaseResponse
from encryption.jwt.jwttoken import TokenUitl
from encryption.x25519.x25519 import X25519MUtil
from cache.redis.redis import RedisClient


router = APIRouter(prefix="/llm")



# Health check endpoint
# Allows to check if the server is running by opening http://IP:8000/llm/health in your browser
@router.get("/health")
async def health()->BaseResponse:
    data = {
        "status":"ok"
    }
    return BaseResponse.success(data=data)


@router.get("/shakeHand/{token}")
async def shake_hands(token:str)->BaseResponse:
    #decrypt token
    data = TokenUitl.decode_token(token=token)
    #generate x25519 keypair
    private_key, public_key =  X25519MUtil.generate_keypair()
    #generate aes key
    aes_key = X25519MUtil.generate_data_encrypting_key(private_key,data["pico_public_key"])
    #put aes key into redis
    RedisClient.set(f"aes_key:{data["target_id"]}",aes_key)
    return BaseResponse.success(data=public_key)


@router.get("/disconnect/{target_id}")
async def disconnect(target_id:str)->BaseResponse:
    # delete aes key in Redis
    RedisClient.delete(f"aes_key:{target_id}")
    return BaseResponse.success()