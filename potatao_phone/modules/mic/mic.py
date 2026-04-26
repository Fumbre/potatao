
import time
import struct
import I2S
import event

# init mic I2S
mic_I2S = I2S.mic

def init():
    # Create a buffer for reading:
    # 256 samples * 4 byte (32 bits) = 1024 byte
    buf = bytearray(1024)

    print("Start reading from Mic")

    try:
        while event.recording:
            # Read data from I2S into buffer
            num_read = mic_I2S.readinto(buf)
            
            # convert DataIN from buffer using 4 byte (32-bit number)
            for i in range(0, num_read, 4):
                # Unpuck 4 byte into number
                sample = struct.unpack('<i', buf[i:i+4])[0]
                
                # INMP441 — 24-bit.
                # often data comes shifted.
                sample >>= 8 # normolize sound
                
                # Put to serial
                print(sample)
                
    except KeyboardInterrupt:
        print("Stop reading from Mic!")
    finally:
        # good
        mic.deinit()
        print("Mic is unpuged")