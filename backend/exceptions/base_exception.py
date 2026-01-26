
class BaseServiceException(Exception):
    def __init__(self, code:int, msg: str):
        self.code = code
        self.msg = msg


class AuthException(BaseServiceException):
    pass

class BusinessException(BaseServiceException):
    pass
