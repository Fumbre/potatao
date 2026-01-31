from pydantic import BaseModel,Field,field_validator,EmailStr
from pydantic_core.core_schema import ValidationInfo
from exceptions.base_exception import BaseServiceException
import phonenumbers

class RegisterUser(BaseModel):
    username:str = Field(min_length=1,max_length=20)
    nickname:str = Field(min_length=1,max_length=20)
    email:EmailStr
    # phone:str
    password:str = Field(min_length=8,max_length=20)
    
    @field_validator("username","nickname",mode="before")
    @classmethod
    def not_blank(cls,v:str,info:ValidationInfo):
        if not v.strip():
            raise BaseServiceException(code=400,msg=f"{info.field_name} is empty!")
        return v

    
    # @field_validator("phone",mode="before")
    # def validate_phone(cls,v:str):
    #     if not v.strip():
    #         raise BaseServiceException(code=400,msg="phone number is empty!")
        
    #     try:
    #         number = phonenumbers.parse(v,"NL")
    #     except phonenumbers.NumberParseException:
    #         raise BaseServiceException(code=400,msg="Invalid phone number!")
    #     if not phonenumbers.is_valid_number(number):
    #         raise BaseServiceException(code=400,msg="Invalid phone number!")
    #     return phonenumbers.format_number(number,phonenumbers.PhoneNumberFormat.E164)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str):
      if not v.strip():
         raise BaseServiceException(code=500, msg="Password is empty!")
      v = v.strip()
      if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
         raise BaseServiceException(code=500, msg="Password must contain letters and numbers!")
      return v    