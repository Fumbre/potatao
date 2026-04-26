
from machine import I2S, Pin
import struct

class Mic:
    def __init__(self, i2s_id: int, sck_pin: int, ws_pin: int, sd_pin: int, btn_trigger_pin):
        self.mic_I2S: I2S = I2S(
            i2s_id, 
            sck=Pin(sck_pin), 
            ws=Pin(ws_pin), 
            sd=Pin(sd_pin),
            mode=I2S.RX,           # moude Sygnal Receiver
            bits=32,               # INMP441 gives data in 32-bit buckets
            format=I2S.MONO,       # mono format
            rate=16000,            # Sampling frequency (16kHz is more than enough for tests) "
            ibuf=1024              # nternal buffer
        )

        self.buf = bytearray(1024)

        # global statement for recording
        self.recording = False

        def handleClick(pin):
            # Toggle the recording state whenever button is pressed
            self.recording = not self.recording
            print("Interrupt triggered! Recording:", self.recording)

        # Set up the pin with an Interrupt Request (IRQ)
        button = Pin(btn_trigger_pin, Pin.IN, Pin.PULL_UP)
        button.irq(trigger=Pin.IRQ_FALLING, handler=handleClick)


    def start(self):
        
        num_read = self.mic_I2S.readinto(self.buf)
            
        # convert DataIN from buffer using 4 byte (32-bit number)
        for i in range(0, num_read, 4):
            # Unpuck 4 byte into number
            sample = struct.unpack('<i', self.buf[i:i+4])[0]
            
            # INMP441 — 24-bit.
            # often data comes shifted.
            sample >>= 8 # normolize sound
            
            # Put to serial
            print(sample)
    
    def end(self):
        self.mic_I2S.deinit()
        print("Mic is unpuged")
