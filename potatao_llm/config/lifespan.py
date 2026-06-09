from contextlib import asynccontextmanager
from fastapi import FastAPI
from encryption.jwt.jwttoken import TokenUitl
from encryption.aes.aes import AESUtil
from encryption.x25519.x25519 import X25519MUtil
from translation.processer import TranslatorProcesser
from cache.redis.redis import RedisClient
from tools.http.http import HttpUtil
import json

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
FASTER_WHISPER_MODEL = os.getenv("FASTERWHISPER_MODEL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
REDIS_HOST= os.getenv("REDIS_HOST")
REDIS_PORT= os.getenv("REDIS_PORT")
REDIS_DB= os.getenv("REDIS_DB")
REDIS_PASSWORD= os.getenv("REDIS_PASSWORD")
REDIS_MAX_CONNECTION= int(os.getenv("REDIS_MAX_CONNECTION"))
ZERO_BASE_URL = os.getenv("ZERO_BASE_URL")
LANGUAGE_API = os.getenv("LANGUAGE_API")

@asynccontextmanager
async def lifespan(app:FastAPI):
    ## init llm mode
    TranslatorProcesser.init(faster_whisper_model=FASTER_WHISPER_MODEL,ollama_model=OLLAMA_MODEL)
    ## init jwt token util
    TokenUitl.init(secrect_key=SECRET_KEY)
    ## init aes util
    AESUtil.init()
    ## init x25519 util
    X25519MUtil.init(secret_key=SECRET_KEY)
    #init redis client
    RedisClient.init(ip=REDIS_HOST,port=REDIS_PORT,db=REDIS_DB,password=REDIS_PASSWORD,max_connection=REDIS_MAX_CONNECTION)
    ## init http util
    HttpUtil.init(base_url=ZERO_BASE_URL)
    # get language data
    language_list = await HttpUtil.get(url=LANGUAGE_API)
    #put language list into redis
    RedisClient.set("lang_list",json.dumps(language_list))
    print("potatao llm start successfully!")
    yield
    print("potatao llm close successfully!")