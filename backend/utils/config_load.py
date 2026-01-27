from pathlib import Path
import yaml
import fnmatch
import socket

def load_local_config(path:str) -> dict:
     base_config = Path(__file__).parent.parent
     config_path = base_config / path /"config" / "application.yaml"
     with open(config_path,"r",encoding="utf-8") as f:
         return yaml.safe_load(f)

def path_match(path: str, patterns:list[str]) -> bool:
     for pattern in patterns:
        normalized = pattern.replace("**", "*")
        if fnmatch.fnmatch(path,normalized):
            return True
        return False

def get_local_ip() ->str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip