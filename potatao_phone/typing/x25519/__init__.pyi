from typing import Union

BASE_POINT: bytes

def calculate(scalar: Union[bytes, bytearray, memoryview], point: Union[bytes, bytearray, memoryview]) -> bytes:
    ...


def generate_keypair()->tuple:
    ...    