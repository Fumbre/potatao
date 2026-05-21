from machine import Pin
from libs.conf.pins import LED_PIN_REC_BTN, SWITCH_PIN_REC_BTN
from libs.display.ui.tools.debounce_effect import Debounce

class RecordButton:
    def __init__(self, mic):
        self.led = Pin(LED_PIN_REC_BTN, Pin.OUT)
        self.mic = mic
        self.led.value(0)

        self.debounce = Debounce(SWITCH_PIN_REC_BTN, self._handle_toggle)

    
    def _handle_toggle(self):
        # Toggle recording state on each valid press
        self.mic_is_recording = not self.mic_is_recording

        if self.mic_is_recording:
            self.led.value(1)
        else:
            self.led.value(0)

