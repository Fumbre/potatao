import requests
from libs.conf.env import load_env
from requests import Response

LANGUAGE_DICT:dict = {}

def init_language():
    global LANGUAGE_DICT
    config = load_env()
    url =  f"http://{config.get('ZERO_IP','')}:{config.get('ZERO_PORT','')}{config.get('LANGUAGE_LIST_API','')}"
    requests.get(url=url)
    response:Response =  requests.get(url=url)
    response_json = response.json()
    print
    data = list(response_json["data"])
    LANGUAGE_DICT = {
    item["language_name"]: {k: v for k, v in item.items() if k not in ["id", "language_name"]}
    for item in data}
    
    print(LANGUAGE_DICT)
    