from libs.display.ui.ui import UI
from libs.display.ui.state_manager import StateManager
from machine import Pin
import utime

from libs.conf.pins import PIN_BTN_AGREE, PIN_BTN_CANCEL, PIN_BTN_HOME, PIN_ENC_A, PIN_ENC_B, PIN_REC_LED, PIN_REC_BTN

from libs.display.ui.tools.debounce_effect import Debounce

# ── FLAGS (set by IRQ, read by main loop) ────────────────
flags = {
    "agree":         False,
    "cancel":        False,
    "home":          False,
    "encoder_delta": 0,
    "ui_update":     True,   # force first render
    "recording":     False,  
}

# ── SETUP ────────────────────────────────────────────────
ui    = UI()
state = StateManager()

# test rooms — later this comes from backend
state.set_rooms(["WiFi Room", "NRF Room", "SD Card", "Settings"])

# ── IRQ HANDLERS ─────────────────────────────────────────
def on_agree(pin):
    flags["agree"] = True
    flags["ui_update"] = True

def on_cancel(pin):
    flags["cancel"] = True
    flags["ui_update"] = True

def on_home(pin):
    flags["home"] = True
    flags["ui_update"] = True

# encoder A/B edge detection

def on_encoder(delta):      # ← add delta parameter
    flags["encoder_delta"] += delta
    flags["ui_update"] = True

ENCODER_TABLE = {
    (1,1,0,1): +1,   # right
    (1,1,1,0): -1,   # left
}

class EncoderDebounce:
    def __init__(self, pin_a, pin_b, callback):
        self.enc_a    = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.enc_b    = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self._prev    = (self.enc_a.value(), self.enc_b.value())

        self.enc_a.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._handle
        )
        self.enc_b.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._handle
        )

    def _handle(self, pin):
        curr = (self.enc_a.value(), self.enc_b.value())
        key  = self._prev + curr   # 4-tuple

        if key in ENCODER_TABLE:
            self.callback(ENCODER_TABLE[key])

        self._prev = curr

enc_debounce = EncoderDebounce(
    pin_a=PIN_ENC_A,
    pin_b=PIN_ENC_B,

    callback=on_encoder,
)



Pin(PIN_BTN_AGREE,  Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_agree)
Pin(PIN_BTN_CANCEL, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_cancel)
Pin(PIN_BTN_HOME,   Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_home)
test = Pin(20,    Pin.IN, Pin.PULL_UP)


# ── RENDER ───────────────────────────────────────────────
def render():
    screen = state.current_screen()
    cursor = state.cursor()

    if screen == "ROOM_LIST":
        ui.render_header("Potatao Menu", inverted=True)
        ui.render_main(state.get_rooms(), cursor)
        ui.render_footer("ENC=move Green=enter Red=back")

    elif screen == "ROOM_VIEW":
        room = state.current_context().get("room", "")
        ui.render_header(room, inverted=True)
        ui.render_main(["Record", "Files", "Back"], cursor)
        ui.render_footer("OK=sel BCK=back")

    elif screen == "RECORDING":
        room = state.current_context().get("room", "")
        ui.render_header(f"REC {room}", inverted=True)
        ui.render_main(["Recording...", "Press REC stop"], 0)
        ui.render_footer("REC=stop")

    elif screen == "FILE_LIST":
        ui.render_header("Files", inverted=True)
        ui.render_main(["(empty)"], 0)
        ui.render_footer("BCK=back")

    elif screen == "SETTINGS":
        ui.render_header("Settings", inverted=True)
        ui.render_main(["Volume", "Sample Rate", "Back"], cursor)
        ui.render_footer("OK=sel BCK=back")

    ui.flush()

# ── SPLASH ───────────────────────────────────────────────
ui.splash("POTATAO", "Starting...")
utime.sleep(1)

# ── MAIN LOOP ────────────────────────────────────────────
print("Starting main loop...")
state.debug()

try:
    while True:
        if test.value() == 0:
            print("Switch is ON / Latched")
        else:
            print("Switch is OFF")
            
        # process flags
        if flags["agree"]:
            flags["agree"] = False
            state.agree()
            state.debug()   # print state after every action

        if flags["cancel"]:
            flags["cancel"] = False
            state.cancel()
            state.debug()

        if flags["home"]:
            flags["home"] = False
            state.go_home()
            state.debug()

        if flags["encoder_delta"] != 0:
            delta = flags["encoder_delta"]
            flags["encoder_delta"] = 0
            state.move_cursor(delta)
            state.debug()

        # render only when dirty
        if flags["ui_update"]:
            flags["ui_update"] = False
            render()

        # small yield — lets MicroPython handle IRQs
        utime.sleep_ms(15)

except KeyboardInterrupt:
    print("Stopped")