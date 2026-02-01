from pydantic import BaseModel,Field,EmailStr
from utils.decoration.validator import NotBlank,Password

class RegisterUser(BaseModel):
    username:NotBlank("username") = Field(min_length=1,max_length=20)
    nickname:NotBlank("nickname") = Field(min_length=1,max_length=20)
    email:EmailStr
    # phone:str
    password:Password("password") = Field(min_length=8,max_length=20)


class LoginUser(BaseModel):
   account:NotBlank("username")
   password:Password("password")
   