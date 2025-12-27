import datetime
import zoneinfo
from rgbmatrix import graphics
from .base import Screen


class ClockScreen(Screen):
    name = "Clock"

    def __init__(self, font_path: str):
        self.font = graphics.Font()
        self.font.LoadFont(font_path)
        self.tz = zoneinfo.ZoneInfo("America/Chicago")
        self.color = graphics.Color(255, 255, 255)

        # Optional: update string once per second (reduces work)
        self._accum = 0.0
        self._cached = ""

    def on_enter(self):
        self._accum = 999.0  # force refresh

    def update(self, dt: float):
        self._accum += dt
        if self._accum >= 0.2:  # refresh 5x/sec so seconds tick feels snappy
            self._accum = 0.0
            now = datetime.datetime.now(self.tz)
            self._cached = now.strftime("%H:%M:%S")

    def draw(self, canvas):
        canvas.Clear()
        # y is baseline; tune as you like for your font
        graphics.DrawText(canvas, self.font, 2, 12, self.color, self._cached)
