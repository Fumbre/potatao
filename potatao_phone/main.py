import time
from libs.mic.mic import Mic
from libs.wifi.wifi import Wifi

def setup():
    global mic, wifi
    mic = Mic(0,16,17,18, 14)
    wifi = Wifi('Cumpose', '4835PjX7q8558')

setup()

wifi.connect()

try:
    while True:
        mic.process()
finally:
    mic.deinit()