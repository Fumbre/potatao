import usqlite
import sdcard

from libs.conf.env import load_env
from libs.conf.pins import *

from libs.display.ui.ui import UI
from libs.data_query.ui import get_view
from libs.db.db import db_create, db_exist
from libs.wifi.wifi import Wifi
from libs.mic.mic import Mic
from libs.speaker.speaker import Speaker
from libs.nrf24.nrf24l01 import NRF24L01

from libs.managers.event_manager import EventManager
from libs.managers.state_manager import StateManager
from libs.managers.function_manager import FunctionManager

import utime
import os
import gc

from machine import Pin, SPI

import uasyncio

# this a async loop
loop = uasyncio.get_event_loop()

gc.collect()

# TODO: 
# - make a setup function for every setup
# - make a setup until main loop


# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(PIN_SDCARD_CLK), mosi=Pin(PIN_SDCARD_MOSI), miso=Pin(PIN_SDCARD_MISO))
sd = sdcard.SDCard(spi, Pin(PIN_SDCARD_CS))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

#os.remove("/sd/potatao.db")

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
# wifi.connect()

#setup Mic
mic = Mic(0, PIN_MIC_SCK, PIN_MIC_WS, PIN_MIC_SD)


# setup nrf
csn = Pin(PIN_NRF_CSN, Pin.OUT, value=1)
ce = Pin(PIN_NRF_CE, Pin.OUT, value=0)

spi = SPI(
    0,
    baudrate=8_000_000,
    polarity=0,
    phase=0,
    sck=Pin(PIN_NRF_SCK),
    mosi=Pin(PIN_NRF_MOSI),
    miso=Pin(PIN_NRF_MISO)
)

nrf = NRF24L01(
    spi,
    csn,
    ce,
    channel=46,
    payload_size=32
)

# Speaker setup
speaker = Speaker(
    i2s_id  = 1,                    # 1, cuz mic uses 0
    sck_pin = PIN_SPEAKER_AMP_SCK,  # GP2
    ws_pin  = PIN_SPEAKER_AMP_WS,   # GP3
    sd_pin  = PIN_SPEAKER_AMP_SD    # GP4
)

# Managers
state_manager = StateManager()
event_manager = EventManager(state_manager)
function_manager = FunctionManager(
    state_manager = state_manager,
    db            = db,
    wifi          = wifi,
    nrf           = nrf,     
    mic           = mic,
    sd            = sd,
    speaker       = speaker,
)
state_manager.function_manager = function_manager


# Pre Render setup
view_list = get_view(db, 0)
state_manager.push_stack(view_list)

# ── MAIN LOOP ────────────────────────────────────────────


async def _yield():
    await uasyncio.sleep(0)

loop.run_until_complete(_yield())

try:
    while True:
        # when Mic is recording audio
        if state_manager.is_recording:
            function_manager.write_chunk() # after write chunk clear memory

        # connect to wifi and backend
        elif state_manager.is_wifi_connecting:
            is_connected = function_manager.wifi_connect()
            if is_connected:
                ui.rerender(state_manager.current_stack(), state_manager.cursor(), state_manager.get_scroll_offset())
                function_manager.connect_to_backend() # connect to backend

        # send audio stream to backend
        elif state_manager.is_wifi_sending:
            function_manager.send_wifi_chunk()

        # nrf send an audio file
        elif state_manager.is_nrf_sending:
            function_manager._send_nrf_chunk()
        
        # nrf receive 
        elif state_manager.is_nrf_receiving:
            function_manager._receive_nrf_chunk()

        # audio is playing to speakers
        elif state_manager.is_playing:
             function_manager._play_speaker()
             
        # listen translated audio     
        elif state_manager.is_wifi_receiving:
            function_manager.receiving_translated_audio()     
        # nothing in state manager going
        # let processor rest
        else:
            utime.sleep_ms(15)
        
        # 
        loop.run_until_complete(_yield())
            
        if event_manager.process():
            gc.collect() # collect garbage memory on rerender
            ui.rerender(state_manager.current_stack(), state_manager.cursor(), state_manager.get_scroll_offset())
            if state_manager.is_recording:
                ui.notify(state_manager.rec_destination, "Recording...")
            if state_manager.is_wifi_connecting:
                ui.notify("Wifi is", "Connecting...")
            state_manager.debug()

        


except KeyboardInterrupt:
    function_manager.stop_recording() 
    db.close()
    os.umount("/sd")
    print("Stopped")
    