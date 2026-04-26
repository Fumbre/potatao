from machine import I2S, Pin

# -- PINS --
SCK_PIN = 26   # Serial Clock (BCLK)
WS_PIN = 27    # Word Select (LRCK)
SD_PIN = 28    # Serial Data (OUT)

# -- I2S initialization protocol --
mic = I2S(
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