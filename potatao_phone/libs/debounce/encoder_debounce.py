from machine import Pin

# Standard State-Transition lookup table for Rotary Encoders
ENCODER_TABLE = {
    (1, 1, 0, 1): +1,   # CW / Right
    (1, 1, 1, 0): -1,   # CCW / Left
}

class EncoderDebounce:
    """Manages raw rotary encoder pin state-transitions cleanly."""
    def __init__(self, pin_a, pin_b, callback):
        self.enc_a    = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.enc_b    = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self._prev    = (self.enc_a.value(), self.enc_b.value())

        self.enc_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._handle)
        self.enc_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._handle)

    def _handle(self, pin):
        curr = (self.enc_a.value(), self.enc_b.value())
        key  = self._prev + curr

        if key in ENCODER_TABLE:
            self.callback(ENCODER_TABLE[key])

        self._prev = curr
