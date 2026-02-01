from model.sso_model import SysUser,select
from database.database_config import SessionLocal

def selectUserList()->list[SysUser]:
    db = SessionLocal()
    try:
        user_list =  db.scalars(select(SysUser).where(SysUser.status == '1')).all()
        return user_list
    finally:
        db.close()

async def selectUserList_async():
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, selectUserList)