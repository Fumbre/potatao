from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select,or_
from sqlalchemy.orm import Session

from common.database.db import DB
from common.exception.base import BusinessException
from common.response.base_response import BaseResponse
from model.llm_model import Language
from request.language_request import LanguageRequest
from response.language_response import LanguageResponse

router = APIRouter(prefix="/language")




@router.post("/insert")
async def insert_language(language_request:LanguageRequest,db:Session=Depends(DB.get_session))->BaseResponse:
    ## check this language whether has already in the database
    try:
        stmt = select(Language).where(
            or_(
                Language.language_name == language_request.language_name,
                Language.iso_code == language_request.iso_code,
                Language.binary_code == language_request.binary_code
            )
        )
        conflict = db.scalar(stmt)
        if conflict:
            raise BusinessException(code=500, message="Language already exists")

        lang = Language(**language_request.model_dump(exclude_unset=True))
        db.add(lang)
        db.commit()
    except Exception as ex:
        db.rollback()
        raise BusinessException(code=500,message=str(ex))
    return BaseResponse.success()


@router.get("/info")
async def language_detail(id:int, db: Session = Depends(DB.get_session))->BaseResponse[LanguageResponse]:
    lang = db.scalar(select(Language).where(Language.id == id))
    lang_response = LanguageResponse.model_validate(lang)
    return BaseResponse.success(data=lang_response)


@router.put("/update")
async def update_language(language_request:LanguageRequest,db:Session=Depends(DB.get_session))->BaseResponse:
    try:
        stmt = select(Language).where(
            or_(
                Language.language_name == language_request.language_name,
                Language.iso_code == language_request.iso_code,
                Language.binary_code == language_request.binary_code
            ),
            Language.id != language_request.id
        )

        raw = db.scalar(stmt)
        if raw:
            raise BusinessException(code=500, message="Language already exists")

        lang = db.scalar(select(Language).where(Language.id == language_request.id))
        lang.language_name = language_request.language_name
        lang.iso_code = language_request.iso_code
        lang.binary_code = language_request.binary_code
        db.commit()
    except Exception as ex:
        db.rollback()
        raise BusinessException(code=500,message=str(ex))
    return BaseResponse.success()


@router.get("/list")
async def language_list(db:Session = Depends(DB.get_session))->BaseResponse[list[LanguageResponse]]:
    data =  db.scalars(select(Language)).all()
    result = []
    for lang in data:
        lang_response = LanguageResponse.model_validate(lang)
        result.append(lang_response)
    return BaseResponse.success(data=result)


@router.delete("/delete")
async def delete_language(id:int, db:Session = Depends(DB.get_session))->BaseResponse:
    try:
        stmt = select(Language).where(Language.id == id)
        lang = db.scalar(stmt)
        if not lang:
            raise BusinessException(code=500, message="Language does not exist")
        db.delete(lang)
        db.commit()
    except Exception as ex:
        db.rollback()
        raise BusinessException(code=500,message=str(ex))
    return BaseResponse.success()
