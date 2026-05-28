from machine import Pin, SPI
from libs.nrf24.nrf24l01 import NRF24L01
import sdcard
import os
import struct
import utime

# =========================================================
# SD CARD
# =========================================================

# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# =========================================================
# NRF24
# =========================================================

csn = Pin(5, Pin.OUT, value=1)
ce = Pin(1, Pin.OUT, value=0)

radio_spi = SPI(
    0,
    baudrate=8_000_000,
    polarity=0,
    phase=0,
    sck=Pin(6),
    mosi=Pin(7),
    miso=Pin(0)
)

nrf = NRF24L01(
    radio_spi,
    csn,
    ce,
    channel=46,
    payload_size=32
)

nrf.set_power_speed(3, 2)

address = b"1Node"

nrf.open_tx_pipe(address)

# =========================================================
# FILE
# =========================================================

file_path = "/sd/LID.wav"

f = open(file_path, "rb")

seq = 0

print("START TX")

try:

    while True:

        # 28 bytes because:
        # 4 bytes seq + 28 bytes data = 32 bytes

        chunk = f.read(28)

        if not chunk:
            break

        # pad last packet
        if len(chunk) < 28:
            chunk += bytes(28 - len(chunk))

        packet = struct.pack("<I", seq) + chunk

        try:

            nrf.send(packet)

            print("TX", seq)

        except Exception as e:

            print("SEND FAIL:", e)

            nrf.flush_tx()
            nrf.flush_rx()

        seq += 1

        utime.sleep_ms(1)

finally:

    f.close()

    os.umount("/sd")

    print("DONE")