# libs/display/ui/state_manager.py

class StateManager:
    def __init__(self):
        self._stack   = []
        self._cursors = {}
        self.is_recording = False
        self.push("MAIN", {})

    def push(self, screen: str, context: dict = {}):
        self._stack.append([screen, dict(context)])

    def pop(self):
        if len(self._stack) > 1:
            self._stack.pop()

    def depth(self) -> int:
        """how deep in the stack we are — useful for back button logic"""
        return len(self._stack)

    def current_screen(self) -> str:
        return self._stack[-1][0]

    def current_context(self) -> dict:
        return self._stack[-1][1]

    def cursor(self) -> int:
        return self._cursors.get(self.current_screen(), 0)

    def move_cursor(self, delta: int, max_items: int):
        if self.is_recording:
            return
        screen  = self.current_screen()
        current = self._cursors.get(screen, 0)
        self._cursors[screen] = (current + delta) % max_items

    def reset_cursor(self, screen: str = None):
        key = screen or self.current_screen()
        self._cursors[key] = 0

    # ── DEBUG ────────────────────────────────────────────

    def debug(self):
        print(f"Stack depth: {self.depth()}")
        for i, (screen, ctx) in enumerate(self._stack):
            print(f"  [{i}] {screen} {ctx}")
        print(f"  cursor={self.cursor()} recording={self.is_recording}")
        # print(f"  list={self._list}") view list of rendered item