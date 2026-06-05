import os
from machine import Pin, SPI
import time

class WavPlayer:
    def __init__(self, speaker_instance):
        self.speaker = speaker_instance
        # Размер куска должен совпадать с размером in_buf в спикере (1024 байта = 512 сэмплов)
        self.chunk_size = 1024 
        self.file_buf = bytearray(self.chunk_size)
        self.mv = memoryview(self.file_buf)

    def play_file(self, filepath):
        print(f"Playing: {filepath}")
        
        # 1. Открываем файл в бинарном режиме на чтение
        try:
            f = open(filepath, "rb")
        except OSError:
            print("Ошибка: Файл не найден")
            return

        # 2. Пропускаем WAV-заголовок (первые 44 байта), чтобы дойти до сырых PCM данных
        f.seek(44)

        # Инициализируем динамик перед началом воспроизведения
        self.speaker.init()

        try:
            while True:
                # Читаем ровно 1024 байта прямо в наш заранее выделенный буфер
                bytes_read = f.readinto(self.file_buf)
                
                # Если файл закончился, выходим из цикла
                if bytes_read == 0:
                    break
                
                # Если считали меньше, чем 1024 (конец файла), берем только этот хвостик
                if bytes_read < self.chunk_size:
                    self.speaker.play_chunk(self.mv[:bytes_read])
                    break
                
                # Отправляем кусок в спикер (там Си-модуль расширит его до 32-бит и отправит в I2S)
                self.speaker.play_chunk(self.file_buf)
                
        except Exception as e:
            print("Ошибка во время воспроизведения:", e)
            
        finally:
            # Обязательно закрываем файл и тушим I2S, чтобы освободить память и пины
            f.close()
            self.speaker.deinit()
            print("Playback finished")