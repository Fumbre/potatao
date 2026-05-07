from machine import Pin, I2C
import time

i2c = I2C(1, sda=Pin(6), scl=Pin(7), freq=100_000)

# Try to send a single command directly
try:
    # Turn display off
    i2c.writeto(0x3C, bytes([0x80, 0xAE]))
    print("Command sent successfully!")
except Exception as e:
    print(f"Failed: {e}")

# Try with lower frequency
try:
    i2c2 = I2C(1, sda=Pin(6), scl=Pin(7), freq=10_000)
    i2c2.writeto(0x3C, bytes([0x80, 0xAE]))
    print("Command at 10kHz sent successfully!")
except Exception as e:
    print(f"Failed at 10kHz: {e}")

    