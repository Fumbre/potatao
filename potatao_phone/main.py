# import time
from libs.mic.mic import Mic
from libs.wifi.wifi import Wifi
from libs.conf.env import load_env
import socket


config = load_env()
SSID = config.get("SSID", "")
WIFI_PASSWORD = config.get("WIFI_PASSWORD", "")

def setup():
    global mic, wifi
    mic = Mic(0,16,17,18, 14)
    wifi = Wifi(SSID, WIFI_PASSWORD)

setup()

wifi.connect()

# Setup UDP Socket
server_ip = config.get("SERVER_IP", "") # Your computer's IP
server_port = int(config.get("SERVER_PORT", ""))
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        mic.process(sock=sock, server_ip=server_ip, server_port=server_port)
finally:
    mic.deinit()