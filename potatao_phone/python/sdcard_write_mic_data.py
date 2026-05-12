from machine import SPI, Pin, I2S
import os
import ssdcard
import struct

# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = ssdcard.SDCard(spi, Pin(13))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")

# Mic setup
mic = I2S(0,
    sck=Pin(16), ws=Pin(17), sd=Pin(18),
    mode=I2S.RX,
    bits=32,
    format=I2S.MONO,
    rate=8000,
    ibuf=4096      # bigger buffer = more tolerance for Python slowness
)

print("Recording 3 seconds...")

buf = bytearray(1024)
mv = memoryview(buf)
out_buf = bytearray(512)  # 16-bit output is half the size

GAIN = 6
total_bytes = 0
target_bytes = 8000 * 2 * 6  # 3 seconds of 16-bit mono at 8000Hz

with open("/sd/test_record.wav", "wb") as f:
    # write placeholder WAV header — we'll fix it after
    f.write(bytearray(44))
    
    while total_bytes < target_bytes:
        num_read = mic.readinto(buf)
        if num_read > 0:
            # convert 32-bit to 16-bit
            for i in range(0, num_read, 4):
                sample = struct.unpack('<i', mv[i:i+4])[0]
                sample >>= 16
                sample *= GAIN
                sample_16 = max(min(sample, 32767), -32768)
                struct.pack_into('<h', out_buf, (i // 2), sample_16)
            
            f.write(out_buf[:num_read // 2])
            total_bytes += num_read // 2

print(f"Recorded {total_bytes} bytes")

# Fix WAV header now we know the size
with open("/sd/test_record.wav", "rb+") as f:
    # write proper WAV header
    num_samples = total_bytes // 2
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + total_bytes, b'WAVE',
        b'fmt ', 16, 1, 1,
        8000, 16000, 2, 16,
        b'data', total_bytes
    )
    f.seek(0)
    f.write(header)

mic.deinit()
os.umount("/sd")
print("✅ Saved to /sd/test_record.wav")
print("Copy it to PC and listen!")