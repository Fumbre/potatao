from libs.mic.mic import Mic
from libs.wifi.wifi import Wifi
from libs.conf.env import load_env
from potatao_phone.libs.display.ui.ui import UI
from libs.display.ui.components.language.Language_settings import LanguageSettings  
from libs.display.ui.events.btn_record import RecordButton
import socket
import utime

from machine import Pin


config = load_env()
SSID = config.get("SSID", "")
WIFI_PASSWORD = config.get("WIFI_PASSWORD", "")

def setup():
    global mic, wifi, ui, language_settings, btn_rec
    mic = Mic(0, 16, 17, 18)
    wifi = Wifi(SSID, WIFI_PASSWORD)
    ui = UI()
    language_settings = LanguageSettings()
    btn_rec = RecordButton(mic)

setup()
wifi.connect()

# Setup UDP Socket
server_ip = config.get("SERVER_IP", "") # Your computer's IP
server_port = int(config.get("SERVER_PORT", ""))
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

last_ui_state = ''
ui_state = "wifi_room" # or "nrf_room"
first_sdcard = True


a = Pin(19, Pin.IN, Pin.PULL_UP)
b = Pin(20, Pin.IN, Pin.PULL_UP)
last_a = a.value()

try:

    while True:

        if not btn_rec.pressed:
            utime.sleep(0.05)

            if ui_state != last_ui_state:
                # ui.oled.draw_screen(ui_state)  # only when changed
                # ui.oled.show()
                last_ui_state = ui_state

            # detect edge on A (this is a test code for encoder)
            if a.value() == 0:
                print("LEFT ⟲")
                ui.make_white()
            if b.value() == 0:
                print("RIGHT ->")
                ui.make_black()
            # if 

            

                
        # if ui_state == 'wifi_room':
            # mic.process(sock=sock, server_ip=server_ip, server_port=server_port)
             
        # mic.process(sock=sock, server_ip=server_ip, server_port=server_port)
        # utime.sleep(0.05)

finally:
    mic.deinit()


# try:

#     while True:
#         if not mic.is_recording:
#             ui.oled.fill(0)
#             ui.oled.text(f"Lang: {language_settings.get_language()}", 0, 0, 1)
#             ui.oled.show()
#             utime.sleep(0.05)
#         mic.process(sock=sock, server_ip=server_ip, server_port=server_port)
#             # if test:
#                 # test = False
#                 # ui.oled.fill(0)
#                 # ui.oled.text("Recorded", 0, 0, 1)
#                 # ui.oled.show()
        
#         # utime.sleep(0.05)

# finally:
#     mic.deinit()

