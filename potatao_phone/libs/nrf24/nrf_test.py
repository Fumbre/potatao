from machine import Pin, SPI
import time
from libs.nrf24.nrf24l01 import NRF24L01

# SPI setup (your pins)
spi = SPI(0,
          sck=Pin(6),
          mosi=Pin(7),
          miso=Pin(4),
          baudrate=1000000)

nrf = NRF24L01(spi, cs=Pin(14), ce=Pin(17))

while True:
    message = b'Hello Pico'
    print("Sending:", message)
    nrf.send(message)
    time.sleep(1)