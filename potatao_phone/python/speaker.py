from machine import I2S, Pin
import mic_dsp

class Speaker:
    VOLUME = 4  # Множитель громкости

    def __init__(self, i2s_id, sck_pin, ws_pin, sd_pin):
        self._i2s_id  = i2s_id
        self._sck_pin = sck_pin
        self._ws_pin  = ws_pin
        self._sd_pin  = sd_pin
        self.spk_I2S  = None

        # Предаллоцируем буферы, чтобы не насиловать GC
        self.in_buf   = bytearray(1024)   # Сюда прилетает 16-битный звук (из сети/файла)
        self.out_buf  = bytearray(2048)   # Сюда С-модуль развернет 32-битный звук
        self.mv_out   = memoryview(self.out_buf)

    def init(self):
        if self.spk_I2S is not None:
            return
        self.spk_I2S = I2S(
            self._i2s_id,
            sck=Pin(self._sck_pin),
            ws=Pin(self._ws_pin),
            sd=Pin(self._sd_pin),
            mode=I2S.TX,        # <-- Режим передачи (Transmitter)
            bits=32,            # Если твой ЦАП жрет 16 бит, можно поставить 16 и убрать Си-конвертер
            format=I2S.MONO,
            rate=24000,
            ibuf=8192
        )

    # Метод принимает 16-битный сырой кусок звука (например, вынутый из сетевого пакета)
    def play_chunk(self, raw_16bit_data):
        if not raw_16bit_data:
            return
        
        # Копируем данные во входной буфер
        length = len(raw_16bit_data)
        self.in_buf[:length] = raw_16bit_data
        
        # Си гонит 16-бит в 32-бит за микросекунды
        bytes_to_write = mic_dsp.expand(memoryview(self.in_buf)[:length], self.out_buf, self.VOLUME)
        
        # Скармливаем готовый 32-битный поток в шину I2S
        self.spk_I2S.write(self.mv_out[:bytes_to_write])

    def deinit(self):
        if self.spk_I2S is None:
            return
        self.spk_I2S.deinit()
        self.spk_I2S = None
        print("Speaker deinitialized")