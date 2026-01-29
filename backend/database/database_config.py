from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine  = None
SessionLocal = None

def init_db(config:dict):
    global engine, SessionLocal
    database_url = str(config["url"])
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()    
        
