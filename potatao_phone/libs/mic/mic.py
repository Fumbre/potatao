
from machine import I2S, Pin
import struct
import time

class Mic:
    GAIN = 14

    def __init__(self, i2s_id: int, sck_pin: int, ws_pin: int, sd_pin: int, btn_trigger_pin):
        self.mic_I2S: I2S = I2S(
            i2s_id, 
            sck=Pin(sck_pin), 
            ws=Pin(ws_pin), 
            sd=Pin(sd_pin),
            mode=I2S.RX,           # moude Sygnal Receiver
            bits=32,               # INMP441 gives data in 32-bit buckets
            format=I2S.MONO,       # mono format
            rate=8000,            # Sampling frequency (16kHz is more than enough for tests) "
            ibuf=2048              # internal buffer
        )

        self.buf = bytearray(1024)
        self.mv = memoryview(self.buf) # Use memoryview to avoid RAM garbage
        self.is_recording = False
        
        # Set up the button
        self.button = Pin(btn_trigger_pin, Pin.IN, Pin.PULL_UP)
        
        # IRQ Handlers: Only change the flag, NO PRINTING or READING here
        self.button.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._handle_button)

    def _handle_button(self, pin):
        # If button is 0 (pressed), start. If 1 (released), stop.
        if pin.value() == 0:
            self.is_recording = True
        else:
            self.is_recording = False

    def process(self, sock, server_ip, server_port):
        """Call this in your main loop"""
        if self.is_recording:
            num_read = self.mic_I2S.readinto(self.buf)
            if num_read > 0:

                # 1. We create a smaller buffer to hold 16-bit packed data 
                # (Sending 32-bit over Wi-Fi is a waste of bandwidth)
                out_buf = bytearray(num_read // 2) 
                
                for i in range(0, num_read, 4):
                    # Unpack 32-bit
                    sample = struct.unpack('<i', self.mv[i:i+4])[0]
                    sample >>= 16 # 24-bit
                    
                    # Convert to 16-bit (CD Quality) for the network
                    # This cuts your Wi-Fi traffic in half!
                    # sample_16 = max(min(sample >> 8, 32767), -32768)

                    sample *= self.GAIN

                    sample_16 = max(min(sample, 32767), -32768)
                    struct.pack_into('<h', out_buf, (i // 2), sample_16)
                
                # 2. Send the WHOLE buffer at once (1024 bytes)
                # NEVER send one sample at a time. Send chunks!
                try:
                    sock.sendto(out_buf, (server_ip, server_port))
                except:
                    pass
        else:
            # If not recording, we give the CPU a tiny rest
            time.sleep(0.05)

    def deinit(self):
        self.mic_I2S.deinit()
        print("Mic deinitialized")