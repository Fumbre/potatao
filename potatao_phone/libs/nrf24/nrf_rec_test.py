from machine import Pin, SPI
import time
from libs.nrf24.nrf24l01 import NRF24L01

# SPI setup (same as TX)
spi = SPI(0,
          sck=Pin(6),
          mosi=Pin(7),
          miso=Pin(4),
          baudrate=1000000)

# Create NRF object
nrf = NRF24L01(spi, cs=Pin(14), ce=Pin(17))

# MUST match transmitter
address = b'abcde'

# Open pipe for receiving
nrf.open_rx_pipe(0, address)

# Start listening
nrf.start_listening()

print("Receiver listening...")

while True:
    if nrf.any():
        data = nrf.recv()
        print("Received:", data)
    time.sleep(0.1)