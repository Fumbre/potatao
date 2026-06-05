from libs.nrf24.nrf24l01 import NRF24L01
from machine import Pin, SPI
import os
import sdcard
import struct
import utime

# =========================================================
# SD CARD
# =========================================================

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

nrf.set_power_speed(1, 1)

address = b"1Node"

nrf.open_rx_pipe(0, address)

nrf.start_listening()

print("RX READY")

# =========================================================
# OUTPUT FILE
# =========================================================

output_path = "/sd/received.wav"

f = open(output_path, "wb")

last_packet = utime.ticks_ms()

last_seq = -1

try:

    while True:

        while nrf.any():

            try:

                packet = nrf.recv()

                last_packet = utime.ticks_ms()

                seq = struct.unpack("<I", packet[:4])[0]

                data = packet[4:]

                # packet loss detect
                if last_seq != -1:

                    if seq != last_seq + 1:

                        lost = seq - last_seq - 1

                        print("LOST:", lost)

                last_seq = seq

                f.write(data)

                print("RX", seq)

            except Exception as e:

                print("RX ERROR:", e)

                nrf.flush_rx()

        # stop after silence
        if utime.ticks_diff(
            utime.ticks_ms(),
            last_packet
        ) > 3000:
            break

finally:

    f.close()

    os.umount("/sd")

    print("DONE")
