from sqlalchemy import String, Integer, LargeBinary
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from common.database.base import Base

class Language(Base):
    __tablename__ = "llm_language"
    language_name:Mapped[str] = mapped_column("language_name",String,nullable=False)
    iso_code:Mapped[str] = mapped_column("iso_code",String,nullable=False)
    binary_code:Mapped[bytes] = mapped_column("binary_code",LargeBinary,nullable=False)