class ScreenManager:
    """
    Owns which screen is active and routes input events.

    Rule:
      1) Current screen gets first chance: current.handle(event)
      2) If it returns False, apply global fallback:
         - ROTATE changes screens
    """

    def __init__(self, screens):
        if not screens:
            raise ValueError("ScreenManager requires at least one screen.")
        self.screens = screens
        self.idx = 0
        self.screens[self.idx].on_enter()

    @property
    def current(self):
        return self.screens[self.idx]

    def _switch_to(self, new_idx: int):
        if new_idx == self.idx:
            return
        self.current.on_exit()
        self.idx = new_idx
        self.current.on_enter()

    def next(self):
        new_idx = (self.idx + 1) % len(self.screens)
        self._switch_to(new_idx)

    def prev(self):
        new_idx = (self.idx - 1) % len(self.screens)
        self._switch_to(new_idx)

    def handle(self, event: dict):
        # Screen-local first
        if self.current.handle(event):
            return

        # Global fallback: rotate changes screen
        if event.get("type") == "ROTATE":
            if event.get("delta", 0) > 0:
                self.next()
            else:
                self.prev()
