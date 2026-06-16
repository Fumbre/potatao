class FakeI2S:
    RX = "RX"; MONO = "MONO"
    def __init__(self, *a, **kw):
        self.rate = kw.get('rate')
        self.bits = kw.get('bits')
        self.mode = kw.get('mode')


    def readinto(self, buf):
        for i in range(len(buf)): buf[i] = 1
        return len(buf)
    

    def deinit(self): 
        pass


class FakePin:
    def __init__(self, n): 
        pass

import sys
sys.modules['machine'] = type(sys)('machine')
sys.modules['machine'].I2S = FakeI2S
sys.modules['machine'].Pin = FakePin
sys.modules['mic_dsp'] = type(sys)('mic_dsp')
sys.modules['mic_dsp'].convert = lambda src, dst, gain: 512

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'mic'))
from mic import Mic

mic = Mic(0, 10, 11, 12)

# not initialized yet
assert mic.mic_I2S is None
assert mic.GAIN == 12

# after init
mic.init()
assert mic.mic_I2S is not None
assert mic.mic_I2S.rate == 24000

# process returns data
result = mic.process()
assert result is not None

# deinit clears it
mic.deinit()
assert mic.mic_I2S is None

print("mic tests passed!")

