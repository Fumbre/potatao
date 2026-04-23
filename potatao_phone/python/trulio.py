from machine import I2S, Pin
import struct

# Настройки пинов I2S
SCK_PIN = 26
WS_PIN = 27
SD_PIN = 28
# Кнопка (подключи между GPIO 15 и GND)
BUTTON_PIN = 15

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

mic = I2S(
    0, 
    sck=Pin(SCK_PIN), ws=Pin(WS_PIN), sd=Pin(SD_PIN),
    mode=I2S.RX, bits=32, format=I2S.MONO,
    rate=16000, ibuf=2048
)

buf = bytearray(1024)

print("READY") # Сигнал для компа, что мы на связи

try:
    while True:
        # Если кнопка нажата (0, так как PULL_UP)
        if button.value() == 0:
            num_read = mic.readinto(buf)
            if num_read > 0:
                # Шлем сырые байты прямо в USB порт
                import sys
                sys.stdout.buffer.write(buf[:num_read])
        else:
            # Маленькая пауза, чтобы не грузить проц, когда кнопка не нажата
            import time
            time.sleep(0.1)
finally:
    mic.deinit()