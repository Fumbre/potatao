from sso.config.sso_confg import app
from sso.controller.sso_conctroller import router as sso_router

app.include_router(sso_router)
