from machine import I2S, Pin
import time
import struct

# --- Настройки пинов (подправь под свои, если отличаются) ---
SCK_PIN = 26   # Serial Clock (BCLK)
WS_PIN = 27    # Word Select (LRCK)
SD_PIN = 28    # Serial Data (OUT с микрофона)

# --- Инициализация микрофона ---
mic = I2S(
    0, 
    sck=Pin(SCK_PIN), 
    ws=Pin(WS_PIN), 
    sd=Pin(SD_PIN),
    mode=I2S.RX,           # Режим ПРИЕМА
    bits=32,               # INMP441 выдает данные в 32-битных слотах
    format=I2S.MONO,       # Берем один канал
    rate=16000,            # Частота дискретизации (16кГц за глаза для тестов)
    ibuf=1024              # Внутренний буфер
)

# Создаем буфер для чтения (на 256 сэмплов)
# 256 сэмплов * 4 байта (32 бита) = 1024 байта
buf = bytearray(1024)

print("Начинаю слушать эфир... Жми Ctrl+C для стопа")

try:
    while True:
        # Читаем данные из I2S в буфер
        num_read = mic.readinto(buf)
        
        # Разбираем буфер по 4 байта (32-битные целые числа)
        # 'i' означает signed int (32 бита)
        # Мы читаем порциями по 4 байта из того, что реально пришло
        for i in range(0, num_read, 4):
            # Распаковываем 4 байта в число
            sample = struct.unpack('<i', buf[i:i+4])[0]
            
            # Тонкий момент: INMP441 — 24-битный. 
            # Часто данные приходят сдвинутыми. Делаем сдвиг, чтобы нормировать звук:
            sample >>= 8
            
            # Выплевываем в Serial Monitor
            print(sample)
            
except KeyboardInterrupt:
    print("Стопэ!")
finally:
    mic.deinit()
    print("Микрофон отключен.")