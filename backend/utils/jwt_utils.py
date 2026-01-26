import jwt
from jwt import InvalidTokenError
from nacos.nacos_life import service_config_from_nacos

def create_access_token(information:dict) -> str:
    secret_key = service_config_from_nacos["token"]["secret_key"]
    algorithm = service_config_from_nacos["token"]["algorithm"]
    token = jwt.encode(information,secret_key,algorithm)
    return token


def verify_access_token(token:str) -> dict:
    secret_key = service_config_from_nacos["token"]["secret_key"]
    algorithm = service_config_from_nacos["token"]["algorithm"]
    try:
      information =  jwt.decode(token,secret_key,algorithms=algorithm)
      if information is None:
         raise ValueError("Invalid token!")
      return information
    except InvalidTokenError:
       raise ValueError("Invalid token!")