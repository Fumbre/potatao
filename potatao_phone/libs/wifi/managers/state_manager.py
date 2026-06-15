# libs/managerss/state_manager.py

class StateManager:
    def __init__(self, function_manager = None):
        self._stack   = []
        self._cursors = {1: 0}
        self.is_recording = False
        self.is_receiving  = False        
        self.is_nrf_sending = False
        self.is_nrf_receiving = False
        self.is_playing = False
        self.rec_destination = "sd" # "wifi" | "nrf" | "sd"
        self.function_manager = function_manager
        self.prefer_language = "en" # "en" | "ru" | "tr"

    def push_stack(self, context: dict = {}):
        self._stack.append(context)

    def pop_stack(self):
        if len(self._stack) > 1:
            self._stack.pop()

    def depth(self) -> int:
        """how deep in the stack we are — useful for back button logic"""
        return len(self._stack)

    def current_stack(self) -> dict:
        return self._stack[-1]
    
    def _max_items_count(self) -> int:
        return len(self._stack[-1])
    
    def cursor(self) -> int:
        return self._cursors.get(self.depth(), 0)
    
    def reset_cursor(self):
        key = self.depth()
        self._cursors[key] = 0
    
    def get_scroll_offset(self, visible_count=4) -> int:
        """
        Calculates how much the menu needs to shift upwards 
        so the selected item stays visible on screen.
        """
        cursor = self.cursor()
        
        # If the cursor moves past the bottom of the visible screen window,
        # push the scroll window down down
        if cursor >= visible_count:
            return cursor - visible_count + 1
            
        return 0

    # ── Handlers ────────────────────────────────────────────

    def handle_scroll(self, delta: int):
        if self.is_recording:
            return False
        
        screen  = self.depth()
        current = self._cursors.get(screen, 0)
        self._cursors[screen] = (current + delta) % self._max_items_count()
        return True


    def handle_agree(self):
        if self.is_recording:
            return False
         
        menu_selected = self.cursor()
        current_item  = self.current_stack()[menu_selected]
        function_name = current_item["function_name"]
        print(function_name)
        return self.function_manager.execute(function_name, current_item)


    
    def handle_cancel(self):
        if self.is_recording:
            return False
        if self.is_playing:
            self.function_manager._stop_speaker()
            return True
        
        if self.depth() > 1:
            # Wipe out old nested track pointers to prevent index overlap bugs
            if self.depth() in self._cursors:
                del self._cursors[self.depth()]
            self.pop_stack()
            return True
        return False
    
    def handle_home(self):
        if self.is_recording:
            return False
        if self.is_playing:
            self.function_manager._stop_speaker()
            return True
        
        # Only reset if we aren't recording and aren't already on the home screen
        if self.depth() > 1:
            self._stack   = [self._stack[0]]
            self._cursors = {1: 0}
            return True
        if self.depth() == 1:
            self._cursors = {1: 0}
            return True 
        return False
    
    def handle_recording(self, pressed: bool):
        if self.is_playing:
            self.function_manager._stop_speaker()
        
        if pressed and not self.is_recording:
            self.is_recording = True
            self.function_manager.start_recording()

        elif not pressed and self.is_recording:
            self.is_recording = False
            self.function_manager.stop_recording()


    # ── DEBUG ────────────────────────────────────────────

    def debug(self):
        print(f"Stack depth: {self.depth()}")
        for i, (ctx) in enumerate(self._stack):
            print(f"  [{i}] {ctx}")
        print(f"  cursor={self.cursor()} recording={self.is_recording}")
        # print(f"  list={self._list}") view list of rendered item