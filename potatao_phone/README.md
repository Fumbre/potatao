# potatao phone

## FRESH START
git submodule update --init --recursive

## Build
./build_build_micropython

## Files that should be on Pico

1. folder: libs
2. file: .env
3. main.py

## Native SD card module

The firmware includes a native MicroPython module named `sdcard`.

```python
from machine import SPI, Pin
import os
import sdcard

spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
os.mount(os.VfsFat(sd), "/sd")
```
