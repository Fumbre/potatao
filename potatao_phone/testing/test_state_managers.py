import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'managers'))
from state_manager import StateManager

class FakeFunctionManager:
    def execute(self, fn, item): 
        return True
    
    def start_recording(self): 
        pass

    def stop_recording(self): 
        pass

    def _stop_speaker(self): 
        pass

fm = FakeFunctionManager()
sm = StateManager(function_manager=fm)
sm.push_stack({0: {"name": "WiFi", "function_name": "link"},
               1: {"name": "NRF", "function_name": "link"},
               2: {"name": "SD Card", "function_name": "link"}})

# test cursor starts at 0
assert sm.cursor() == 0

# test scroll works
sm.handle_scroll(1)
assert sm.cursor() == 1

# test scroll wraps
sm.handle_scroll(1)
sm.handle_scroll(1)
assert sm.cursor() == 0

# test recording blocks scroll
sm.is_recording = True
sm.handle_scroll(1)
assert sm.cursor() == 0
sm.is_recording = False

# test cancel goes back
sm.push_stack({0: {"name": "Sub", "function_name": "link"}})
assert sm.depth() == 2
sm.handle_cancel()
assert sm.depth() == 1

print("state_manager tests passed!")

