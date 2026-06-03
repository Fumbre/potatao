from contextlib import asynccontextmanager
from fastapi import FastAPI
from common.database.db import DB
from common.redis.redis import RedisClient
from common.aws3.s3 import S3Util
from common.encrptytion.jwt.jwttoken import TokenUitl
from common.encrptytion.aes.aes import AESUtil
from common.encrptytion.x25519.x25519 import X25519MUtil
from service.config.config import settings


@asynccontextmanager
async def lifespan(app:FastAPI):
    print(settings.s3.secret_key)
    ## init db
    DB.init(settings.db.path,settings.db.password)
    ##init redis
    RedisClient.init(ip=settings.redis.host,port=settings.redis.port,password=settings.redis.password,db=settings.redis.db,max_connection=settings.redis.max_connection)
    ##init aws3 client
    S3Util.init(ip=settings.s3.ip,port=settings.s3.port,access_key=settings.s3.access_key,secret_key=settings.s3.secret_key)
    ## init encryption utils
    TokenUitl.init(secrect_key=settings.project.token_secret_key)
    AESUtil.init()
    X25519MUtil.init(secret_key=settings.project.token_secret_key)
    print("potatao station start successfully!")
    yield
    print("potatao station close successfully!")