class FakeI2S:
    TX = "TX"; MONO = "MONO"
    def __init__(self, *a, **kw):
        self.mode = kw.get('mode')
        self.rate = kw.get('rate')
        self.bits = kw.get('bits')
        self.written = []


    def write(self, data): 
        self.written.append(bytes(data))


    def deinit(self): 
        pass


class FakePin:
    def __init__(self, n): 
        pass

import sys
sys.modules['machine'] = type(sys)('machine')
sys.modules['machine'].I2S = FakeI2S
sys.modules['machine'].Pin = FakePin

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'speaker'))
from speaker import Speaker

sp = Speaker(1, 16, 17, 18)

# not initialized yet
assert sp.speaker_I2S is None

# after init
sp.init()
assert sp.speaker_I2S is not None
assert sp.speaker_I2S.bits == 16
assert sp.speaker_I2S.rate == 24000

# play chunk writes data
chunk = bytes([1, 2, 3, 4] * 10)
sp.play_chunk(chunk)
assert sp.speaker_I2S.written[0] == chunk

# deinit
sp.deinit()
assert sp.speaker_I2S is None

print("speaker tests passed!")

