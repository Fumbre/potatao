from gateway.app import app
from utils.config_load import load_local_config,get_local_ip
import uvicorn

if __name__ == "__main__":
    config = load_local_config("gateway")
    uvicorn.run(
        "gateway.app:app",
        host=get_local_ip(),
        port=int(config["server"]["port"]),
        reload=True
    )