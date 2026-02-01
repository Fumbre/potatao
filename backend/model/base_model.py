from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import BigInteger,DateTime,func
from sqlalchemy.orm import Mapped,mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    id:Mapped[int] = mapped_column("ID",BigInteger,nullable=False,primary_key=True,autoincrement=False)
    createTime:Mapped[datetime]  = mapped_column("CREATE_TIME",DateTime,nullable=False,default=func.now())

    def to_dict(self) -> dict:
        """
        Convert SQLAlchemy ORM instance to dict.

        - datetime -> "YYYY-MM-DD HH:MM:SS"
        - int ID fields -> str
        """
        result = {}
        for attr in self.__mapper__.attrs:
            try:
                value = getattr(self, attr.key)
                if isinstance(value, datetime):
                    result[attr.key] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, int) and (attr.key.endswith("Id") or attr.key == "id"):
                    result[attr.key] = str(value)
                else:
                    result[attr.key] = value
            except AttributeError:
                continue
        return result