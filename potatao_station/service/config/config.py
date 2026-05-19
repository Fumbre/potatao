from pydantic import BaseModel
from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent[2]


class DBSettings(BaseModel):
    db_path:str = "potatao.db"
    password:str = "123456"


class RedisSettings(BaseModel):
    host:str = "127.0.0.1"
    port:int = 6379
    db:int = 0
    password:str = "123456"
    max_connection = 10


class AWS3Settings(BaseModel):
    ip:str = "127.0.0.1"
    port:int = 5001
    access_key:str = "adfafhjfhajsf"
    secret_key:str = "wrjqwrqwe"
    
class CustomSettings(BaseModel):
    token_secret_key:str = "abcdefghijklmnopqrstuvwxyz"


class AppSettings(BaseSettings):
    db:DBSettings = DBSettings()
    redis:RedisSettings = RedisSettings()
    project:CustomSettings = CustomSettings()
    s3:AWS3Settings = AWS3Settings()


config = SettingsConfigDict(
    env_file= PROJECT_ROOT/ ".env",
    env_file_encoding="utf-8",
    env_nested_delimiter="__",
    extra="ignore"
)

settings = AppSettings()