# libs/display/ui/state_manager.py

class StateManager:

    # ── INIT ────────────────────────────────────────────

    def __init__(self):
        # screen stack — each entry is [screen_name, context_dict]
        self._stack   = []

        # cursor position remembered per screen name
        self._cursors = {}

        # dynamic room list from backend
        self._rooms = []

        # recording state
        self.is_recording = False

        # start on room list screen
        self.push("ROOM_LIST", {})

    # ── SCREEN STACK ────────────────────────────────────

    def push(self, screen: str, context: dict = {}):
        self._stack.append([screen, dict(context)])

    def pop(self):
        if len(self._stack) > 1:
            self._stack.pop()

    def current_screen(self) -> str:
        return self._stack[-1][0]

    def current_context(self) -> dict:
        return self._stack[-1][1]

    def depth(self) -> int:
        """how deep in the stack we are — useful for back button logic"""
        return len(self._stack)

    # ── CURSOR ──────────────────────────────────────────

    def cursor(self) -> int:
        return self._cursors.get(self.current_screen(), 0)

    def move_cursor(self, delta: int):
        """moves cursor by delta, wraps around based on current screen items"""
        if self._ui_locked(): return
         
        count = self._item_count()
        if count == 0:
            return
        screen  = self.current_screen()
        current = self._cursors.get(screen, 0)
        self._cursors[screen] = (current + delta) % count

    def reset_cursor(self):
        self._cursors[self.current_screen()] = 0

    def _item_count(self) -> int:
        """returns how many items current screen has for cursor wrapping"""
        screen = self.current_screen()
        if screen == "ROOM_LIST":
            return len(self._rooms)
        elif screen == "ROOM_VIEW":
            return 3   # Record, Files, Back
        else:
            return 0

    # ── ROOMS (dynamic from backend) ────────────────────

    def set_rooms(self, rooms: list):
        self._rooms = list(rooms)
        self.reset_cursor()   # reset cursor when list changes

    def get_rooms(self) -> list:
        return self._rooms

    def rooms_count(self) -> int:
        return len(self._rooms)

    def selected_room(self) -> str:
        """returns name of currently highlighted room"""
        idx = self.cursor()
        if self._rooms and idx < len(self._rooms):
            return self._rooms[idx]
        return ""

    # ── ACTIONS ─────────────────────────────────────────

    def _ui_locked(self) -> bool:
        """returns True when UI input should be ignored"""
        return self.is_recording

    def agree(self):
        """user pressed agree/ok — context depends on current screen"""
        if self._ui_locked(): return
         
        screen = self.current_screen()

        if screen == "ROOM_LIST":
            room = self.selected_room()
            if room:
                self.push("ROOM_VIEW", {"room": room})
                self.reset_cursor()

        elif screen == "ROOM_VIEW":
            cursor = self.cursor()
            if cursor == 0:    # Record
                self.start_recording()
            elif cursor == 1:  # Files
                self.push("FILE_LIST", self.current_context())
                self.reset_cursor()
            elif cursor == 2:  # Back
                self.pop()
    
    def go_home(self):
        """encoder click — clear stack, back to main menu"""
        if self._ui_locked(): return  # record button is physically pressed, ignore all UI
        
        self._stack   = []
        self._cursors = {}
        self.push("ROOM_LIST", {})

    def cancel(self):
        """always go back one level"""
        if self._ui_locked(): return
         
        if len(self._stack) > 1:
            self.pop()

    # ── RECORDING ───────────────────────────────────────

    def start_recording(self):
        self.is_recording = True
        self.push("RECORDING", self.current_context())

    def stop_recording(self):
        self.is_recording = False
        self.pop()
    
    def audio_destination(self) -> dict:
        """only meaningful when is_recording=True"""
        if not self.is_recording:
            return {}
        return self.current_context()

    # ── DESTINATION ─────────────────────────────────────

    def destination(self) -> str:
        """what's the current audio destination"""
        return self.current_context().get("room", "")
    
    # ── DEBUG ────────────────────────────────────────────

    def debug(self):
        print(f"Stack depth: {self.depth()}")
        for i, (screen, ctx) in enumerate(self._stack):
            print(f"  [{i}] {screen} {ctx}")
        print(f"  cursor={self.cursor()} recording={self.is_recording}")
        print(f"  rooms={self._rooms}")