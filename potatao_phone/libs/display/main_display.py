import sys
sys.path.append('/potatao_phone')

from machine import Pin
import time

button_up   = Pin(20, Pin.IN, Pin.PULL_UP)
button_sel  = Pin(21, Pin.IN, Pin.PULL_UP)
button_down = Pin(22, Pin.IN, Pin.PULL_UP)

while True:
    if button_up.value() == 0:
        print("UP pressed")
    if button_sel.value() == 0:
        print("SELECT pressed")
    if button_down.value() == 0:
        print("DOWN pressed")
    time.sleep_ms(100)