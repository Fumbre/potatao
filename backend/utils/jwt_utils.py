import jwt
from jwt import InvalidTokenError
from nacos.nacos_life import service_config_from_nacos
from exceptions.base_exception import AuthException

def create_access_token(information:dict) -> str:
    secret_key = service_config_from_nacos["token"]["secret_key"]
    algorithm = service_config_from_nacos["token"]["algorithm"]
    token = jwt.encode(information,secret_key,algorithm)
    return "Bearer " + token


def verify_access_token(token:str) -> dict:
    secret_key = service_config_from_nacos["token"]["secret_key"]
    algorithm = service_config_from_nacos["token"]["algorithm"]
    try:
      information =  jwt.decode(token,secret_key,algorithms=algorithm)
      if information is None:
         raise AuthException(code=403,msg="Invalid token")
      return information
    except InvalidTokenError:
       raise AuthException(code=403,msg="Invalid token")