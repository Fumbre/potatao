import base64
from typing import Optional, Annotated
from pydantic import BaseModel, BeforeValidator


def decode_base64_to_bytes(v: any) -> bytes:
    if isinstance(v, str):
        return base64.b64decode(v)
    return v

Base64Bytes = Annotated[bytes, BeforeValidator(decode_base64_to_bytes)]


class LanguageRequest(BaseModel):
    id:Optional[int] = None
    language_name:str
    iso_code:str
    binary_code:Base64Bytes