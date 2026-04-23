from machine import I2S, Pin
import os

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
with open('dogbark.wav', 'rb') as f:
    f.seek(44)  # skip WAV header (44 bytes standard)
    while True:
        num_read = f.readinto(buf)
        if num_read == 0:
            break
        speaker.write(buf[:num_read])

print("Done!")
speaker.deinit()