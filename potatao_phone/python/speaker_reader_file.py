from machine import I2S, Pin, SPI
import os
import sdcard


# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# 2. Setup speaker
speaker = I2S(
    0,
    sck=Pin(2),   
    ws=Pin(3),    
    sd=Pin(4),    
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=44100,
    ibuf=32768  # УВЕЛИЧЕНО: 32КБ буфера спасут от треска и падения качества
)

print("Playing LID.wav...")

# 3. Читаем кусками побольше
buf = bytearray(512) # УВЕЛИЧЕНО: так Pico реже дергает карту
with open('/sd/LID.wav', 'rb') as f:
    f.seek(44) 
    while True:
        num_read = f.readinto(buf)
        if num_read == 0:
            break
        speaker.write(buf[:num_read])

print("Done!")
speaker.deinit()
os.umount("/sd")