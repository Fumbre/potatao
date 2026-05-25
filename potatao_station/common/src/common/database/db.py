from pathlib import Path
from threading import Lock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,session,DeclarativeBase

from common.database.base import Base


class DB:
    _engine = None
    _SessionLocal = None
    _lock = Lock()
    
    @classmethod
    def init(cls,path:str,password:str):
        if cls._engine is None:
            with cls._lock:
                if cls._engine is None:
                    abs_path = Path(path).resolve()
                    db_url = f"sqlite:////{abs_path}"
                    cls._engine = create_engine(
                        url=db_url,
                        echo=False,
                        connect_args={"check_same_thread":False}
                    )
                    ## create session
                    cls._SessionLocal = sessionmaker(
                        bind=cls._engine,
                        autoflush=False,
                    )
                    Base.metadata.create_all(bind=cls._engine)
        return cls._engine
    
    
    @classmethod
    def get_session(cls):
        db_session =  cls._SessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()