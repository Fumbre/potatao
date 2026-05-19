from machine import Pin, SPI
from libs.nrf24.nrf24l01 import NRF24L01
import utime

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

nrf = NRF24L01(
    spi,
    csn,
    ce,
    channel=46,
    payload_size=16
)

address = b"1Node"

nrf.open_rx_pipe(0, address)

nrf.start_listening()

print("Listening...")

while True:

    while nrf.any():

        data = nrf.recv()

        msg = data.decode().strip('\x00')

        print("Received:", msg)

    utime.sleep_ms(10)