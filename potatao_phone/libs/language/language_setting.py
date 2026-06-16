import requests
from libs.conf.env import load_env
from requests import Response


def init_language():
    config = load_env()
    url =  f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('LANGUAGE_LIST_API','')}"
    requests.get(url=url)
    response:Response =  requests.get(url=url)
    response_json = response.json()
    data = list(response_json["data"])
    LANGUAGE_DICT = {
    item["language_name"]: {k: v for k, v in item.items() if k not in ["id", "language_name"]}
    for item in data}
    
    return LANGUAGE_DICT
    