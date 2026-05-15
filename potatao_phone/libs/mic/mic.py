from machine import I2S, Pin
import struct
import time

class Mic:
    GAIN = 14

    def __init__(self, i2s_id: int, sck_pin: int, ws_pin: int, 
                 sd_pin: int, btn_trigger_pin):
        self.mic_I2S = I2S(
            i2s_id,
            sck=Pin(sck_pin),
            ws=Pin(ws_pin),
            sd=Pin(sd_pin),
            mode=I2S.RX,
            bits=32,
            format=I2S.MONO,
            rate=16000,
            ibuf=8192 #  8192 | 12288
        )
        self.buf = bytearray(2048)
        self.mv = memoryview(self.buf)
        self.is_recording = False

        # packet tracking
        self.seq_num = 0
        self.record_start_ms = 0

        self.button = Pin(btn_trigger_pin, Pin.IN, Pin.PULL_UP)
        self.button.irq(
            trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING,
            handler=self._handle_button
        )

    def _handle_button(self, pin):
        if pin.value() == 0:
            self.is_recording = True
            self.seq_num = 0                        # reset sequence
            self.record_start_ms = time.ticks_ms()  # reset timestamp
        else:
            self.is_recording = False

    def process(self, sock, server_ip, server_port):
        if self.is_recording:
            num_read = self.mic_I2S.readinto(self.buf)
            if num_read > 0:
                # unpack ALL samples at once — much faster than loop
                num_samples = num_read // 4
                samples = struct.unpack('<' + 'i' * num_samples, self.mv[:num_read])

                # process all samples — still Python but no struct overhead per sample
                audio_buf = bytearray(num_samples * 2)
                for idx, sample in enumerate(samples):
                    sample >>= 16
                    sample *= self.GAIN
                    sample_16 = max(min(sample, 32767), -32768)
                    struct.pack_into('<h', audio_buf, idx * 2, sample_16)

                # header + send
                timestamp_ms = time.ticks_diff(time.ticks_ms(), self.record_start_ms)
                header = struct.pack('<II', self.seq_num, timestamp_ms)

                try:
                    sock.sendto(header + audio_buf, (server_ip, server_port))
                    self.seq_num += 1
                except:
                    pass
        else:
            time.sleep(0.05)

    def deinit(self):
        self.mic_I2S.deinit()
        print("Mic deinitialized")