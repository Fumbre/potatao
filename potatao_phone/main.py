
import usqlite
import sdcard

from libs.conf.pins import PIN_SDCARD_CLK, PIN_SDCARD_MOSI, PIN_SDCARD_MISO, PIN_SDCARD_CS
from libs.db.db import db_create, db_exist

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


# db setup
if not usqlite.mem_status():
    usqlite.mem_status(True)
    
db = usqlite.connect("/sd/potatao.db")
if not db_exist(db):
    db_create(db)
else:
    print("Database already exists, skipping setup")




# verify
rows = db.execute("SELECT * FROM potatao_ui WHERE parent_id=0").fetchall()
print("Main menu items:", rows)


db.close()
os.umount("/sd")