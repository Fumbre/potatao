from machine import I2S, Pin, SPI
import os
import sdcard


# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")


# Setup speaker
speaker = I2S(
    0,
    sck=Pin(2),   # BCLK
    ws=Pin(3),    # LRCK  
    sd=Pin(4),    # DIN to amplifier
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=44100,
    ibuf=4096
)

print("Playing dogbark...")

buf = bytearray(1024)
with open('/sd/test_record.wav', 'rb') as f:
    f.seek(44)  # skip WAV header (44 bytes standard)
    while True:
        num_read = f.readinto(buf)
        if num_read == 0:
            break
        speaker.write(buf[:num_read])

print("Done!")
speaker.deinit()
os.umount("/sd")