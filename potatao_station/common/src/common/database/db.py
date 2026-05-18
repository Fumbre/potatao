from threading import Lock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,session,DeclarativeBase


class DB:
    _engine = None
    _SessionLocal = None
    _lock = Lock()
    
    @classmethod
    def init(cls,path:str,password:str):
        if cls._engine is None:
            with cls._lock:
                if cls._engine is None:
                    db_url = f"sqlite+pysqlcipher://:{password}@/{path}"
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
        return cls._engine
    
    
    @classmethod
    def get_session(cls)->session:
        return cls._SessionLocal            