import sys
from config.gateway_config import app
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.config_load import load_local_config

if __name__ == "__main__":
    import uvicorn
    config = load_local_config("gateway")
    uvicorn.run("gatewayapplication:app",host=config["server"]["host"],port=config["server"]["port"],reload=True)
