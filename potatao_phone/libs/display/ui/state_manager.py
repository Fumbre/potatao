# libs/display/ui/state_manager.py

class StateManager:
    def __init__(self):
        self._stack   = []
        self._cursors = {}
        self.is_recording = False

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

    def move_cursor(self, delta: int):
        if self.is_recording:
            return
        
        screen  = self.depth()
        current = self._cursors.get(screen, 0)
        self._cursors[screen] = (current + delta) % self._max_items_count()

    def reset_cursor(self):
        key = self.depth()
        self._cursors[key] = 0

    # ── DEBUG ────────────────────────────────────────────

    def debug(self):
        print(f"Stack depth: {self.depth()}")
        for i, (ctx) in enumerate(self._stack):
            print(f"  [{i}] {ctx}")
        print(f"  cursor={self.cursor()} recording={self.is_recording}")
        # print(f"  list={self._list}") view list of rendered item