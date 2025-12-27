class Screen:
    name = "Unnamed"

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle(self, event: dict) -> bool:
        """
        Return True if the screen consumed the event.
        """
        return False

    def update(self, dt: float):
        """
        Time-based logic. Called every loop iteration with dt seconds since last frame.
        """
        pass

    def draw(self, canvas):
        """
        Draw current state onto canvas.
        """
        pass
