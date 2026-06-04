from machine import I2S, Pin
import struct
import time
import mic_dsp  # our C module

class Mic:
    GAIN = 12 # sound loudenest

    def __init__(self, i2s_id, sck_pin, ws_pin, sd_pin):
        self._i2s_id  = i2s_id
        self._sck_pin = sck_pin
        self._ws_pin  = ws_pin
        self._sd_pin  = sd_pin
        self.mic_I2S  = None

        self.buf     = bytearray(2048)
        self.mv      = memoryview(self.buf)
        self.out_buf = bytearray(1024)  # preallocated, no GC pressure
        self.seq_num         = 0
        self.record_start_ms = 0

    def init(self):
        if self.mic_I2S is not None:
            return
        self.mic_I2S = I2S(
            self._i2s_id,
            sck=Pin(self._sck_pin),
            ws=Pin(self._ws_pin),
            sd=Pin(self._sd_pin),
            mode=I2S.RX,
            bits=32,
            format=I2S.MONO,
            rate=24000,
            ibuf=8192
        )

    # mic.process() returns ONLY raw audio
    def process(self):
        num_read = self.mic_I2S.readinto(self.buf)
        if num_read > 0:
            bytes_written = mic_dsp.convert(self.mv[:num_read], self.out_buf, self.GAIN)
            return memoryview(self.out_buf)[:bytes_written]
        return None



    # put it somewhere with wifi related
    # wifi sender adds header when needed
    # def send_wifi(chunk, seq_num, record_start_ms):
    #     timestamp_ms = time.ticks_diff(time.ticks_ms(), record_start_ms)
    #     header = struct.pack('<II', seq_num, timestamp_ms)
    #     sock.sendto(header + chunk, (server_ip, server_port))

    # #def process(self, sock, server_ip, server_port):
    # def process(self): 
    #     num_read = self.mic_I2S.readinto(self.buf)
    #     if num_read > 0:
    #         # C does the whole conversion in microseconds
    #         bytes_written = mic_dsp.convert(
    #             self.mv[:num_read],
    #             self.out_buf,
    #             self.GAIN
    #         )

    #         timestamp_ms = time.ticks_diff(
    #             time.ticks_ms(), self.record_start_ms
    #         )
    #         header = struct.pack('<II', self.seq_num, timestamp_ms)

    #         self.seq_num += 1
    #         return header + self.out_buf[:bytes_written]
    #         # try:
    #         #     sock.sendto(
    #         #         header + self.out_buf[:bytes_written],
    #         #         (server_ip, server_port)
    #         #     )
    #         #     self.seq_num += 1
    #         # except:
    #         #     pass
    
            

    def deinit(self):
        if self.mic_I2S is None:
            return
        self.mic_I2S.deinit()
        self.mic_I2S = None
        print("Mic deinitialized")



        