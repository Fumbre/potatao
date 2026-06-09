from pydantic import BaseModel, ConfigDict


class LanguageResponse(BaseModel):
    id:int
    language_name:str
    iso_code:str
    binary_code:bytes

    model_config = ConfigDict(from_attributes=True)