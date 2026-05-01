import time
from libs.mic.mic import Mic
from libs.wifi.wifi import Wifi
import socket

def setup():
    global mic, wifi
    mic = Mic(0,16,17,18, 14)
    wifi = Wifi('Cumpose', '4835PjX7q8558')

setup()

wifi.connect()

# Setup UDP Socket
server_ip = "192.168.1.53" # Your computer's IP
server_port = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        mic.process(sock=sock, server_ip=server_ip, server_port=server_port)
finally:
    mic.deinit()