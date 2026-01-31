from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from sso.requestbody.sso_request_body import RegisterUser
from sqlalchemy.orm import Session
from database.database_config import get_db
from sso.service.sso_service import user_register


router = APIRouter(prefix="/sso")


@router.post("/register")
def register(user:RegisterUser,db:Session = Depends(get_db))->JSONResponse:
    return user_register(user=user,db=db)