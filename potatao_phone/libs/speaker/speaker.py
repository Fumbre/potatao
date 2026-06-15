# libs/speaker/speaker.py
from machine import I2S, Pin

class Speaker:
    def __init__(self, i2s_id, sck_pin, ws_pin, sd_pin):
        self._i2s_id  = i2s_id
        self._sck_pin = sck_pin
        self._ws_pin  = ws_pin
        self._sd_pin  = sd_pin
        self.speaker_I2S = None
        self.buf = bytearray(2048)  # preallocated output buffer

    def init(self):
        if self.speaker_I2S is not None:
            return
        self.speaker_I2S = I2S(
            self._i2s_id,
            sck=Pin(self._sck_pin),
            ws=Pin(self._ws_pin),
            sd=Pin(self._sd_pin),
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO,
            rate=24000,
            ibuf=8192
        )

    def play_chunk(self, chunk: bytes):
        """write one chunk of raw 16-bit mono audio"""
        if self.speaker_I2S is None:
            return
        self.speaker_I2S.write(chunk)

    def deinit(self):
        if self.speaker_I2S is not None:
            self.speaker_I2S.deinit()
            self.speaker_I2S = None