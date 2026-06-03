
from machine import Pin
from libs.conf.pins import PIN_BTN_AGREE, PIN_BTN_CANCEL, PIN_BTN_HOME, PIN_ENC_A, PIN_ENC_B, PIN_BTN_REC
from libs.debounce.encoder_debounce import EncoderDebounce
from libs.managers.state_manager import StateManager


class EventManager:
    def __init__(self, state_manager:StateManager):
        # Pass StateManager as a dependency 
        self.state_manager = state_manager
        
        # Central flag register owned by EventManager
        self.flags = {
            "agree":         False,
            "cancel":        False,
            "home":          False,
            "encoder_delta": 0,
            "ui_update":     True,   # Force first UI draw cycle
            "record":        False,  
        }
        
        # Initialize Hardware Interrupt Routines
        self._setup_irqs()

    def _setup_irqs(self):
        """Initializes raw button pins and configures async hardware interrupts."""
        # Setup push buttons
        Pin(PIN_BTN_AGREE,  Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=self._on_agree)
        Pin(PIN_BTN_CANCEL, Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=self._on_cancel)
        Pin(PIN_BTN_HOME,   Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING, handler=self._on_home)
        Pin(PIN_BTN_REC,    Pin.IN, Pin.PULL_UP).irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._on_rec)
        
        # Setup rotary encoder debouncer, binding directly to an internal class callback
        self.encoder = EncoderDebounce(PIN_ENC_A, PIN_ENC_B, callback=self._on_encoder)

    # ── IRQ HANDLERS (Asynchronous Hardware Execution context) ──
    # Note: MicroPython IRQ handlers must access pre-allocated memory structures
    def _on_agree(self, pin):
        self.flags["agree"] = True

    def _on_cancel(self, pin):
        self.flags["cancel"] = True

    def _on_home(self, pin):
        self.flags["home"] = True

    def _on_rec(self, pin):
        # Toggles recording state
        self.flags["record"] = True

    def _on_encoder(self, delta):
        self.flags["encoder_delta"] += delta

    # ── MAIN SYNCHRONOUS PROCESS LOOP LOOP ──
    def process(self):
        """
        Polls asynchronous ISR flags inside the synchronous main execution loop.
        Processes system interactions, updates StateManager, and informs the caller 
        if the UI requires a re-rendering pass.
        """
        # Save a snapshot copy of the encoder delta and reset it instantly
        # to minimize raw missing pulses during long processing sequences.
        delta = self.flags["encoder_delta"]
        if delta != 0:
            self.flags["encoder_delta"] = 0
            # Inform StateManager that the selector index shifted
            self.flags["ui_update"] = self.state_manager.handle_scroll(delta)

        if self.flags["agree"]:
            self.flags["agree"] = False
            
            self.flags["ui_update"] = self.state_manager.handle_agree()


        if self.flags["record"]:
            self.flags["record"] = False
            # recoring event should be both
            # when we press button
            # when we unpress button
            # based on high or low we put it to state manager.is_recording
            pressed = Pin(PIN_BTN_REC).value() == 0 if True else False
            self.state_manager.handle_recording(pressed)
            self.flags["ui_update"] = True


        if self.flags["cancel"]:
            self.flags["cancel"] = False
            self.flags["ui_update"] = self.state_manager.handle_cancel()

        if self.flags["home"]:
            self.flags["home"] = False
            self.flags["ui_update"] = self.state_manager.handle_home()

        # Check if any event or hardware action flipped the ui_update flag
        if self.flags["ui_update"]:
            self.flags["ui_update"] = False
            return True  # Signal to main loop that UI must re-render!
            
        return False  # No UI render changes needed
    