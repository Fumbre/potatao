
import usqlite
import sdcard

from libs.conf.pins import PIN_SDCARD_CLK, PIN_SDCARD_MOSI, PIN_SDCARD_MISO, PIN_SDCARD_CS
from libs.display.ui.ui import UI
from libs.display.ui.state_manager import StateManager
from libs.display.ui.api.view import get_view
from libs.db.db import db_create, db_exist
from libs.events.event_manager import EventManager

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
ui = UI()

# Starting window
ui.splash("POTATAO", "Starting...")

# DB setup
db = usqlite.connect("/sd/potatao.db")

# create db structure if not exitst
if not db_exist(db):
    db_create(db)

# Managers
state_manager = StateManager()
event_manager = EventManager(state_manager)


# Pre Render setup
view_list = get_view(db, 0)
state_manager.push_stack(view_list)

# ── MAIN LOOP ────────────────────────────────────────────

try:
    while True:
        if event_manager.process():
            ui.rerender(state_manager.current_stack(), state_manager.cursor(), state_manager.get_scroll_offset())
            
            state_manager.debug()

        utime.sleep_ms(15)

except KeyboardInterrupt:
    db.close()
    os.umount("/sd")
    print("Stopped")
    