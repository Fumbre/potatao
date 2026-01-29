from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import BigInteger,DateTime,func
from sqlalchemy.orm import Mapped,mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    id:Mapped[int] = mapped_column("ID",BigInteger,nullable=False,primary_key=True,autoincrement=False)
    createTime:Mapped[datetime]  = mapped_column("CREATE_TIME",DateTime,nullable=False,default=func.now())
