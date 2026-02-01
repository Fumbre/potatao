from typing import Annotated
from pydantic import AfterValidator
from exceptions.base_exception import BaseServiceException

def NotBlank(field_name: str):
    def _check(v: str) -> str:
        if v is None or not v.strip():
            raise ValueError(f"{field_name} is empty!")
        return v.strip()
    return Annotated[str, AfterValidator(_check)]

def Password(field_name: str):

    def _check(v: str) -> str:

        if v is None or not v.strip():
            raise BaseServiceException(
                code=400,
                msg=f"{field_name} is empty!"
            )

        v = v.strip()

        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise BaseServiceException(
                code=400,
                msg=f"{field_name} must contain letters and numbers!"
            )

        return v

    return Annotated[str, AfterValidator(_check)]