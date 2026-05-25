from libs.conf.pins import *
from machine import Pin
import utime

class Debounce:
    DEBOUNCE_MS = 50 # milliseconds that the button must be stable before being pressed

    '''
    pin_number   GPIO pin number
    callback     Function to call when a valid press is detected
    trigger      Pin.IRQ_FALLING (default) or Pin.IRQ_RISING
    '''
    def __init__(self, pin_number: int, callback, trigger: int = Pin.IRQ_FALLING | Pin.IRQ_RISING):
        # not pressed = HIGH (1); pressed =  LOW (0)
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP) 
        self.callback = callback

        # Timestamp of the last detected edge in ms
        self.last_press_ms = 0

        # Last known stable state of the button
        self.last_state = self.pin.value()

        # Attach the IRQ: fires on every edge, debounce logic is inside the handler
        self.pin.irq(trigger=trigger, handler=self._handle)

    # Checks whether enough time has passed since the last edge
    def _handle(self, pin):
        now = utime.ticks_ms()

        # Calculate how many milliseconds have passed since the last edge
        time_passed = utime.ticks_diff(now, self.last_press_ms) 

        # Example: button pressed at 1000ms, bounce happens at 1020ms
        # 1020 - 1000 = 20ms < 50ms >> ignored
        if time_passed < self.DEBOUNCE_MS:
            return
        
        current_state = pin.value()

        # Act when goes from unpressed (1) to pressed (0)
        if self.last_state == 1 and current_state == 0:
            self.callback()

        # Update state and time for the next comparison
        self.last_state = current_state
        self.last_press_ms = now
