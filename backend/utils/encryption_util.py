from passlib.context import CryptContext

generator = CryptContext(schemes=["argon2"], deprecated="auto")

def hash(text:str) -> str:
    return generator.hash(text)

def verify(text:str,hashed_text:str) -> bool:
    return generator.verify(text,hashed_text)