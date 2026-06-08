from typing import TypeVar, Generic, Optional

from pydantic import ConfigDict
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel,Generic[T]):

    code: int
    message: str
    data:Optional[T]


    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    @classmethod
    def success(cls,data: T = None, message: str = "success") -> "BaseResponse":
        return cls(code=200,message=message,data=data)

    @classmethod
    def error(cls,code:int=500,message: str = "fail") -> "BaseResponse":
        return cls(code=code,message=message)


    @classmethod
    def response(cls,code:int,message:str,data:T=None) -> "BaseResponse":
        return cls(code=code,message=message,data=data)