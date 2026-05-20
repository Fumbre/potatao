from libs.mic.mic import Mic
from libs.nrf24.nrf_tx_test import send_sound_sample
from libs.conf.env import load_env
import socket
import utime


config = load_env()

def setup():
    global mic, wifi, ui, language_settings
    mic = Mic(0, 16, 17, 18, 22)

    

setup()


# Setup UDP Socket
server_ip = config.get("SERVER_IP", "") # Your computer's IP
server_port = int(config.get("SERVER_PORT", ""))
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:

    while True:
        if not mic.is_recording:
            continue
        sample = mic.process()
        send_sound_sample(sample)
            # if test:
                # test = False
                # ui.oled.fill(0)
                # ui.oled.text("Recorded", 0, 0, 1)
                # ui.oled.show()
        
        # utime.sleep(0.05)

finally:
    mic.deinit()

