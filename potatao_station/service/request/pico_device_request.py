from typing import TypedDict

from pydantic import BaseModel


class PicoDeviceRequest(BaseModel):
    data: str


class PicoAuthentication(TypedDict):
    machine_id: str
    pico_public_key: str
    prefered_language: str


class CommunicationData(TypedDict):
    data:str
    target_machine_id: str
    is_end: bool