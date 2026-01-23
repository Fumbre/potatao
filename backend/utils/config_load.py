from pathlib import Path
import yaml
import fnmatch

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