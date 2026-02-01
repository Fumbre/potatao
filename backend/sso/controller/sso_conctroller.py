from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from sso.requestbody.sso_request_body import RegisterUser,LoginUser
from sqlalchemy.orm import Session
from database.database_config import get_db
from sso.service.sso_service import user_register,user_login
from fastapi import Request


router = APIRouter(prefix="/sso")


@router.post("/register")
def register(user:RegisterUser,request: Request,db:Session = Depends(get_db))->JSONResponse:
    return user_register(user=user,request=request,db=db)

@router.post("/login")
def login(user:LoginUser,request: Request,db:Session = Depends(get_db)) -> JSONResponse:
    return user_login(user=user,request=request,db=db)