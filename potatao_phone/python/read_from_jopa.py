from libs.speaker.speaker import Speaker
from libs.conf.pins import *
from machine import Pin, SPI
import os
import sdcard

# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(PIN_SDCARD_CLK), mosi=Pin(PIN_SDCARD_MOSI), miso=Pin(PIN_SDCARD_MISO))
sd = sdcard.SDCard(spi, Pin(PIN_SDCARD_CS))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

speaker = Speaker(1, PIN_SPEAKER_AMP_SCK, PIN_SPEAKER_AMP_WS, PIN_SPEAKER_AMP_SD)
speaker.init()

with open("/sd/recordings/record_5.wav", "rb") as f:
    f.read(44)  # skip header
    buf = bytearray(1024)
    while True:
        num_read = f.readinto(buf)
        if num_read == 0:
            break
        speaker.play_chunk(buf[:num_read])

speaker.deinit()
print("done!")