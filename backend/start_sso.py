from utils.config_load import load_local_config,get_local_ip
from sso.config.sso_confg import app

if __name__ == "__main__":
    import uvicorn
    config = load_local_config("sso")
    uvicorn.run("sso.app:app",host=get_local_ip(),port=config["server"]["port"],reload=True)