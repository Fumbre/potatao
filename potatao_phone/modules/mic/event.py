from machine import Pin

# flag to track state
recording = False

def handleClick(pin):
    global recording
    # Toggle the recording state whenever button is pressed
    recording = not recording
    print("Interrupt triggered! Recording:", recording)

# Set up the pin with an Interrupt Request (IRQ)
button = Pin(22, Pin.IN, Pin.PULL_UP)
button.irq(trigger=Pin.IRQ_FALLING, handler=handleClick)
