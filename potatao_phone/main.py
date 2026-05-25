
import usqlite
import sdcard

from libs.conf.pins import PIN_SDCARD_CLK, PIN_SDCARD_MOSI, PIN_SDCARD_MISO, PIN_SDCARD_CS
from libs.display.ui.ui import UI
from libs.display.ui.state_manager import StateManager
from libs.display.ui.api.view import get_view
from libs.db.db import db_create, db_exist

from libs.conf.pins import PIN_BTN_AGREE, PIN_BTN_CANCEL, PIN_BTN_HOME, PIN_ENC_A, PIN_ENC_B, PIN_REC_LED, PIN_REC_BTN


import utime
import os

from machine import Pin, SPI

# TODO: 
# - make a setup function for every setup


# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(PIN_SDCARD_CLK), mosi=Pin(PIN_SDCARD_MOSI), miso=Pin(PIN_SDCARD_MISO))
sd = sdcard.SDCard(spi, Pin(PIN_SDCARD_CS))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# os.remove("/sd/potatao.db")

# Display setup
ui    = UI()
state = StateManager()

# Starting window
ui.splash("POTATAO", "Starting...")
utime.sleep(1)

# DB setup
db = usqlite.connect("/sd/potatao.db")

# create db structure if not exitst
if not db_exist(db):
    db_create(db)



# ── FLAGS (set by IRQ, read by main loop) ────────────────
flags = {
    "agree":         False,
    "cancel":        False,
    "home":          False,
    "encoder_delta": 0,
    "ui_update":     True,   # force first render
    "recording":     False,  
}

# IRQ evnets
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

def on_rec(pin):
    flags["recording"] = not flags["recording"]
    flags["ui_update"] = True


# Encoder deboucer
#==========================================
def on_encoder(delta):
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



# ------- buttons 
Pin(PIN_BTN_AGREE,  Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_agree)
Pin(PIN_BTN_CANCEL, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_cancel)
Pin(PIN_BTN_HOME,   Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=on_home)
Pin(PIN_REC_BTN,    Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=on_rec)


# Render setup
view_list = get_view(db, 0)
state.push_stack(view_list)

# re render
def rerender():
    cursor = state.cursor()

    ui.render_header('Main menu', inverted=False)
    ui.render_main(state.current_stack(), cursor)
    ui.flush()


# ── MAIN LOOP ────────────────────────────────────────────
print("Starting main loop...")
state.debug()

try:
    while True:

        # bug
        # create a good logic for btn pressed and unpressed. 
        # use pin determination (high or low)
        # be sure when we start a phone button is not clicked
        # if so fix tell to state manager that button is clicked when phone was started 
        if flags["recording"] and not state.is_recording:
            flags["recording"] = True
            state.is_recording = True
            state.debug()
        
        if not flags["recording"] and state.is_recording:
            state.is_recording = False
            state.debug()
            
        # process flags
        if flags["agree"]:
            flags["agree"] = False
            state.debug()   # print state after every action

        if flags["cancel"]:
            flags["cancel"] = False
            state.debug()

        if flags["home"]:
            flags["home"] = False
            state.debug()

        if flags["encoder_delta"] != 0:
            delta = flags["encoder_delta"]
            flags["encoder_delta"] = 0
            state.move_cursor(delta)
            state.debug()

        # render only when dirty
        if flags["ui_update"]:
            flags["ui_update"] = False
            print("we are updated")
            rerender()

        utime.sleep_ms(15)

except KeyboardInterrupt:
    db.close()
    os.umount("/sd")
    print("Stopped")
    