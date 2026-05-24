from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from common.database.base import Base


class PicoDevice(Base):
    __tablename__ = "pico_device"
    machine_id:Mapped[str] = mapped_column("machine_id",String,nullable=False,autoincrement=True)