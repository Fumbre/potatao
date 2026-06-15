from machine import ADC, Pin
from conf.pins import *


class VolumeSettings:
    def __init__(self):
        # Initialise the ADC on the potentiometer pin
        self.pot = ADC(Pin(...))

        # Volume percentage (0 to 100)
        self.volume = 0

    def read(self):
        # Read the raw ADC value (0 to 65535 on the Pico)
        adc_value = self.pot.read_u16()

        # Convert raw value to a 0 to 100 percentage
        self.volume = int(adc_value / 65535 * 100)

        return self.volume

    def get_volume(self):
        # Returns the last computed volume percentage
        return self.volume
    
    