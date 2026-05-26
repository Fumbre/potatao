from machine import Pin
from libs.conf.pins import PIN_REC_BTN, PIN_REC_LED
from libs.display.ui.tools.debounce_effect import Debounce
import time
from libs.mic.mic import Mic

class RecordButton:
    def __init__(self, mic: Mic):
        self.btn = Pin(PIN_REC_BTN, Pin.IN, Pin.PULL_UP)
        self.led = Pin(PIN_REC_LED, Pin.OUT)
        self.mic = mic
        self.pressed = False

        self.led.value(0)
        self.debounce = Debounce(PIN_REC_BTN, self._handle_toggle)

    def _handle_toggle(self):
        self.pressed = not self.pressed

        if self.pressed:
            self.led.value(1)
            self.mic.is_recording = True
            self.mic.seq_num = 0
            self.mic.record_start_ms = time.ticks_ms()
        else:
            self.led.value(0)
            self.mic.is_recording = False

            