from sqlalchemy import VARCHAR,CHAR,select,func
from sqlalchemy.orm import Mapped,mapped_column
from model.base_model import Base

class SysUser(Base):
    __tablename__ = "SYS_USER"
    username:Mapped[str] = mapped_column("USER_NAME",VARCHAR(50),nullable=False)
    email:Mapped[str] = mapped_column("EMAIL",VARCHAR(50),nullable=False)
    password:Mapped[str] = mapped_column("USER_PASSWORD",VARCHAR(200),nullable=False)
    nickname:Mapped[str] = mapped_column("NICKNAME",VARCHAR(50),nullable=False)
    avatar:Mapped[str] = mapped_column("AVATAR",VARCHAR(255),nullable=True)
    status:Mapped[str] = mapped_column("STATUS",CHAR(1),nullable=False,default='1')
    

