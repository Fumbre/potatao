
import usqlite
import sdcard

from libs.conf.env import load_env
from libs.conf.pins import PIN_SDCARD_CLK, PIN_SDCARD_MOSI, PIN_SDCARD_MISO, PIN_SDCARD_CS

from libs.display.ui.ui import UI
from libs.data_query.ui import get_view
from libs.db.db import db_create, db_exist
from libs.wifi.wifi import Wifi

from libs.managers.event_manager import EventManager
from libs.managers.state_manager import StateManager
from libs.managers.function_manager import FunctionManager

import utime
import os
import gc

from machine import Pin, SPI

gc.collect()

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

gc.collect()
print(f"Free RAM before DB initialization: {gc.mem_free()} bytes")

# DB setup
db = usqlite.connect("/sd/potatao.db")

# create db structure if not exitst
if not db_exist(db):
    db_create(db)


# conf
config = load_env()


# setup Wifi
wifi = Wifi(config.get("SSID", "") , config.get("WIFI_PASSWORD", ""))

# Managers
state_manager = StateManager()
event_manager = EventManager(state_manager)
function_manager = FunctionManager(
    state_manager = state_manager,
    db            = db,
    wifi          = wifi,
    # nrf           = nrf,     
    # mic           = mic,
)
state_manager.function_manager = function_manager


# Pre Render setup
view_list = get_view(db, 0)
state_manager.push_stack(view_list)

# ── MAIN LOOP ────────────────────────────────────────────

try:
    while True:
        if event_manager.process():
            ui.rerender(state_manager.current_stack(), state_manager.cursor(), state_manager.get_scroll_offset())
            if state_manager.is_recording:
                ui.notify(state_manager.rec_destination, "Recording...")
            state_manager.debug()

        utime.sleep_ms(15)

except KeyboardInterrupt:
    db.close()
    os.umount("/sd")
    print("Stopped")
    