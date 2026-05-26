from machine import Pin, SPI
from libs.nrf24.nrf24l01 import NRF24L01
import os
import sdcard
import struct
import utime

# =========================================================
# SD CARD
# =========================================================

sd_spi = SPI(
    1,
    baudrate=10_000_000,
    sck=Pin(14),
    mosi=Pin(15),
    miso=Pin(12)
)

sd = sdcard.SDCard(sd_spi, Pin(13))

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

# max power + 2mbps
nrf.set_power_speed(3, 2)

address = b"1Node"

nrf.open_rx_pipe(0, address)

nrf.start_listening()

print("NRF RX READY")

# =========================================================
# WAV FILE
# =========================================================

wav_path = "/sd/radio.wav"

wav = open(wav_path, "wb")

# placeholder WAV header
wav.write(bytearray(44))

# =========================================================
# AUDIO BUFFER
# =========================================================

buffer = bytearray(1024)
buffer_mv = memoryview(buffer)

buf_i = 0

total_audio = 0

last_packet_time = utime.ticks_ms()

last_seq = -1

# =========================================================
# RECEIVE LOOP
# =========================================================

try:

    while True:

        # read ALL packets from FIFO
        while nrf.any():

            try:

                packet = nrf.recv()

                last_packet_time = utime.ticks_ms()

                # -----------------------------------------
                # HEADER
                # -----------------------------------------

                seq = struct.unpack("<I", packet[:4])[0]

                audio = packet[4:]

                # -----------------------------------------
                # PACKET LOSS CHECK
                # -----------------------------------------

                if last_seq != -1:

                    if seq != last_seq + 1:

                        lost = seq - last_seq - 1

                        print("PACKETS LOST:", lost)

                last_seq = seq

                # -----------------------------------------
                # BUFFER AUDIO
                # -----------------------------------------

                end = buf_i + len(audio)

                if end <= len(buffer):

                    buffer_mv[buf_i:end] = audio

                    buf_i = end

                # -----------------------------------------
                # WRITE TO SD
                # -----------------------------------------

                if buf_i >= 512:

                    wav.write(buffer_mv[:buf_i])

                    total_audio += buf_i

                    buf_i = 0

            except Exception as e:

                print("RX ERROR:", e)

                nrf.flush_rx()

        # auto stop after silence
        if utime.ticks_diff(
            utime.ticks_ms(),
            last_packet_time
        ) > 3000:
            break

        

finally:

    # =====================================================
    # WRITE REMAINING BUFFER
    # =====================================================

    if buf_i > 0:

        wav.write(buffer_mv[:buf_i])

        total_audio += buf_i

    wav.close()

    # =====================================================
    # FIX WAV HEADER
    # =====================================================

    with open(wav_path, "rb+") as f:

        sample_rate = 8000
        bits_per_sample = 16
        channels = 1

        byte_rate = sample_rate * channels * bits_per_sample // 8

        block_align = channels * bits_per_sample // 8
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + total_audio,
            b'WAVE',
            b'fmt ',
            16,
            1,
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b'data',
            total_audio
        )

        f.seek(0)

        f.write(header)

    os.umount("/sd")

    print("===================================")
    print("DONE")
    print("FILE:", wav_path)
    print("BYTES:", total_audio)
    print("===================================")