from libs.conf.pins import *
from machine import Pin, SPI
import os
import sdcard
import speaker

# 1. SD Card & Filesystem Setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(PIN_SDCARD_CLK), mosi=Pin(PIN_SDCARD_MOSI), miso=Pin(PIN_SDCARD_MISO))
sd = sdcard.SDCard(spi, Pin(PIN_SDCARD_CS))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# 2. Open the file handler explicitly in binary-read mode
audio_path = "/sd/recordings/record_1.wav"

try:
    print(f"Opening audio file: {audio_path}")
    # We must open as 'rb' (raw binary) so it handles raw PCM arrays correctly
    with open(audio_path, "rb") as track:
    
        print(track)
        # Pass the open file stream object into your custom C module.
        # You can adjust sample rate or buffer allocations directly here:
        speaker.play(track, rate=24000, ibuf=2048)
        
    print("Playback finished cleanly.")

except OSError as e:
    print(f"Filesystem Error: Could not find or open the file. {e}")
except Exception as e:
    print(f"Playback crashed: {e}")