# screens/countdown.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rgbmatrix import graphics
from .base import Screen


class CountdownScreen(Screen):
    name = "Countdown"

    def __init__(self, font_path: str):
        self.tz = ZoneInfo("America/Chicago")  # CST/CDT handled automatically
        self.font = graphics.Font()
        self.font.LoadFont(font_path)

        self.color = graphics.Color(0, 255, 255)  # cyan
        self._accum = 0.0
        self._text = ""

        self._recompute_text()

    def _recompute_text(self):
        now = datetime.now(self.tz)
        tomorrow = (now + timedelta(days=1)).date()
        midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, tzinfo=self.tz)
        remaining = int((midnight - now).total_seconds())
        if remaining < 0:
            remaining = 0

        # Format as HH:MM:SS + total seconds
        h = remaining // 3600
        m = (remaining % 3600) // 60
        s = remaining % 60
        self._text = f"{h:02d}:{m:02d}:{s:02d}  ({remaining})"

    def update(self, dt: float):
        # Update once per second (not every frame)
        self._accum += dt
        if self._accum >= 1.0:
            self._accum %= 1.0
            self._recompute_text()

    def draw(self, canvas):
        canvas.Clear()
        graphics.DrawText(canvas, self.font, 1, 12, self.color, "Seconds left today:")
        graphics.DrawText(canvas, self.font, 1, 26, self.color, self._text)
