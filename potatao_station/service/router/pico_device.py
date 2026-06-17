from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from common.aws3.file_type import FileType
from common.aws3.s3 import S3Util
from common.database.db import DB
from common.encrptytion.jwt.jwttoken import TokenUitl
from common.encrptytion.x25519.x25519 import X25519MUtil
from common.exception.base import BusinessException
from common.http.http import HttpUtil
from common.redis.redis import RedisClient
from common.response.base_response import BaseResponse
from model.pico_device_model import PicoDevice
from request.pico_device_request import PicoDeviceRequest, PicoAuthentication
from router.communication import manager
from service.zero_service import store_pefered_language, start_translated_audio_session, stop_translated_audio_session

router = APIRouter(prefix="/pico/device")


@router.post("/register")
async def register(pico_request:PicoDeviceRequest,session:Session = Depends(DB.get_session))->BaseResponse:
    ##parse token
    data = TokenUitl.decode_token(pico_request.data)
    machine_id = data["machine_id"]
    # check whether pico has already registered into zero
    if RedisClient.sexist("pico_device",machine_id):
        raise BusinessException("This machine has already been registered!",500)
    pico = PicoDevice(
        machine_id= machine_id,
    )
    session.add(pico)
    session.commit()
    ## add machine id in Redis
    RedisClient.sadd("pico_device",machine_id)
    return BaseResponse.success()

@router.delete("/remove/{machine_id}")
async def remove(machine_id:str,session:Session = Depends(DB.get_session))->BaseResponse:
    session.query(PicoDevice).filter(PicoDevice.machine_id == machine_id).delete()
    session.commit()
    RedisClient.sremove("pico_device",machine_id)
    return BaseResponse.success()


@router.post("/authorize")
async def pico_authentication(pico_auth:PicoDeviceRequest,db:Session = Depends(DB.get_session))->BaseResponse:
    data = PicoAuthentication(**TokenUitl.decode_token(pico_auth.data))
    if not RedisClient.sexist("pico_device", data["machine_id"]):
        raise BusinessException("This machine does not register, please register firstly!", 500)
    private_key,public_key = X25519MUtil.generate_keypair()
    aes_key = X25519MUtil.generate_data_encrypting_key(private_key,pico_public_key=data["pico_public_key"])
    RedisClient.set(f"pico_data_key:{data['machine_id']}",aes_key)
    session_id = S3Util.start_session(machine_id=data["machine_id"],user_id=data["pico_public_key"],bucket_name="audio",content_type=FileType.WAV)
    RedisClient.set(f"s3_session_id:{data['machine_id']}",session_id)
    language_dict = store_pefered_language(machine_id=data["machine_id"],lang=data["prefered_language"],db=db)
    data_llm = {
        "pico_public_key":public_key,
        "target_id":data["machine_id"]
    }
    llm_token = TokenUitl.generate_token(data_llm)
    result = await HttpUtil.get(url=f"/llm/shakeHand",params={"token":llm_token})
    llm_public_key = result.get("data")
    translated_aes_key = X25519MUtil.generate_data_encrypting_key(private_key,pico_public_key=llm_public_key)
    print(f"[Station] translated_aes_key={translated_aes_key}")  # ← 加这行
    RedisClient.set(f"llm_data_key:{data['machine_id']}",translated_aes_key)
    start_translated_audio_session(original_machine_id=data["machine_id"],language_dict=language_dict,key=llm_public_key)
    return BaseResponse.success(data=public_key)


@router.get("/disconnect/{machine_id}")
async def disconnect(machine_id:str)->BaseResponse:
    # check whether pico has already registered into zero
    await manager.disconnect(machine_id)
    if not RedisClient.sexist("pico_device", machine_id):
        raise BusinessException("This machine does not register, please register firstly!", 500)
    ## delete aes keys from Redis
    RedisClient.delete(f"pico_data_key:{machine_id}")
    RedisClient.delete(f"llm_data_key:{machine_id}")
    ## get session id
    session_id = RedisClient.get(f"s3_session_id:{machine_id}")
    ## finish the S3 uploading session
    S3Util.complete_session(session_id)
    ## delete this session id from redis
    RedisClient.delete(f"s3_session_id:{machine_id}")
    ## stop translated audio updating
    stop_translated_audio_session(machine_id)
    return BaseResponse.success()

@router.get("/registeration/check/{machine_id}")
async def is_registered(machine_id:str)->BaseResponse:
    return BaseResponse.success(data=RedisClient.sexist("pico_device", machine_id))


@router.post("/receive/handshake")
async def receive_hand_shake(pico_auth:PicoDeviceRequest,db:Session = Depends(DB.get_session))->BaseResponse:
    data = PicoAuthentication(**TokenUitl.decode_token(pico_auth.data))
    if not RedisClient.sexist("pico_device", data["machine_id"]):
        raise BusinessException("This machine does not register, please register firstly!", 500)
    private_key, public_key = X25519MUtil.generate_keypair()
    aes_key = X25519MUtil.generate_data_encrypting_key(private_key, pico_public_key=data["pico_public_key"])
    RedisClient.set(f"receive_pico_data_key:{data['machine_id']}", aes_key)
    store_pefered_language(machine_id=data["machine_id"], lang=data["prefered_language"], db=db)
    return BaseResponse.success(data=public_key)


@router.post("/receive/disconnet/{machine_id}")
async def receive_disconnect(machine_id:str)->BaseResponse:
    await manager.disconnect(machine_id)
    RedisClient.delete(f"receive_pico_data_key:{machine_id}")
    return BaseResponse.success()




