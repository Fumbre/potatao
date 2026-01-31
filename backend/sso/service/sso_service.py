from sqlalchemy.orm import Session
from sso.requestbody.sso_request_body import RegisterUser
from fastapi.responses import JSONResponse
from model.sso_model import SysUser,select
from exceptions.base_exception import BaseServiceException
from utils.redisUtils import RedisClient
from utils.snowflake_id_util import get_snowflake_id
from utils.encryption_util import hash
from nacos.nacos_life import SessionLocal
from fastapi import Request

def user_register(db:Session,request:Request,user:RegisterUser)->JSONResponse:
    redis_client: RedisClient = getattr(request.app.state, "redis_client", None)
    #check username, email, phone number exist in Bloom filter
    if redis_client.bloom_exists("bf:sso:username",user.username):
        raise BaseServiceException(code=400,msg= "username exists!")
    if redis_client.bloom_exists("bf:sso:email",user.email):
        raise BaseServiceException(code=400,msg= "email exists!")
    # if redis_client.abloom_exists("bf:sso:phone",user.phone):
    #     raise BaseServiceException(code=400,msg= "phone number exists!")
    newPassword = hash(user.password)
    sysUser = SysUser(
        id = get_snowflake_id(),
        username = user.username,
        email = user.email,
        nickname = user.nickname,
        # phone = user.phone,
        password = newPassword
    )
    try:
        # add username, phone , email into Bloom-filter
        redis_client.bloom_add("bf:sso:username",user.username)
        redis_client.bloom_add("bf:sso:email",user.email)
        # redis_client.abloom_add("cf:phone",user.phone)
        # add user into database
        db.add(sysUser)
        #commit data to database
        db.commit()
        return JSONResponse(
            status_code=200,
            content={
                "code":200,
                "msg":"register success!"
            }
        )
    except Exception as e:
        print(e)
        db.rollback()
        #remove username, phone , email from bloom filter
        redis_client.bloom_remove("bf:sso:username",user.username)
        redis_client.bloom_remove("bf:sso:email",user.email)
        # redis_client.abloom_remove("cf:phone",user.phone)
        raise BaseServiceException(code=500, msg="register failed!")
    finally:
        db.close()



def selectUserList()->list[SysUser]:
    db = SessionLocal()
    try:
        user_list =  db.scalars(select(SysUser).where(SysUser.status == '1')).all()
        return user_list
    finally:
        db.close()