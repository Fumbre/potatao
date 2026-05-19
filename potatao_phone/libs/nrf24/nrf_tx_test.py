from machine import Pin, SPI
from libs.nrf24.nrf24l01 import NRF24L01
import utime

# -----------------------------
# PINS
# -----------------------------

csn = Pin(5, Pin.OUT, value=1)
ce = Pin(1, Pin.OUT, value=0)

spi = SPI(
    0,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(6),
    mosi=Pin(7),
    miso=Pin(0)
)


# -----------------------------
# NRF24
# -----------------------------

nrf = NRF24L01(
    spi,
    csn,
    ce,
    channel=46,
    payload_size=16
)

address = b"1Node"

nrf.open_tx_pipe(address)

counter = 0

print("Transmitter started")

while True:

    msg = "Hello {:03}".format(counter)

    try:

        print("Sending:", msg)

        nrf.send(msg.encode())

        print("SUCCESS")

    except Exception as e:

        print("FAILED:", e)

        # Recover radio
        nrf.flush_tx()
        nrf.flush_rx()

    counter += 1

    # IMPORTANT
    utime.sleep_ms(500)
