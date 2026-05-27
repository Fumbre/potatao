import os
from machine import Pin, SPI
from speaker import Speaker
from wav_player import WavPlayer

# SD setup
spi = SPI(1, baudrate=10_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd")


# --- 2. Создаем объект Спикера ---
# i2s_id=1 (чтобы не конфликтовать с микрофоном, если он на id=0), пины подставь свои
spk = Speaker(i2s_id=1, sck_pin=10, ws_pin=11, sd_pin=12)

# --- 3. Запускаем плеер ---
player = WavPlayer(spk)

# Файл должен быть строго: Стерео/Моно переведенный в Mono, 24000 Гц, 16-бит PCM
player.play_file("/sd/LID.wav")