from machine import I2S, Pin
import time
import struct


# -- PINS --
SCK_PIN = 26   # Serial Clock (BCLK)
WS_PIN = 27    # Word Select (LRCK)
SD_PIN = 28    # Serial Data (OUT)

# -- I2S initialization protocol --
micProtocol = I2S(
    0, 
    sck=Pin(SCK_PIN), 
    ws=Pin(WS_PIN), 
    sd=Pin(SD_PIN),
    mode=I2S.RX,           # moude Sygnal Receiver
    bits=32,               # INMP441 gives data in 32-bit buckets
    format=I2S.MONO,       # mono format
    rate=16000,            # Sampling frequency (16kHz is more than enough for tests) "
    ibuf=1024              # nternal buffer
)

# Create a buffer for reading:
# 256 samples * 4 byte (32 bits) = 1024 byte
buf = bytearray(1024)

print("Start reading from Mic")

try:
    while True:
        # Read data from I2S into buffer
        num_read = micProtocol.readinto(buf)
        
        # convert DataIN from buffer using 4 byte (32-bit number)
        for i in range(0, num_read, 4):
            # Unpuck 4 byte into number
            sample = struct.unpack('<i', buf[i:i+4])[0]
            
            # INMP441 — 24-bit.
            # often data comes shifted.
            sample >>= 8 # normolize sound
            
            # Put to serial
            print(sample)
            
except KeyboardInterrupt:
    print("Stop reading from Mic!")
finally:
    # good
    mic.deinit()
    print("Mic is unpuged")