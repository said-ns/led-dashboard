from rgbmatrix import graphics
from .base import Screen


class TextScreen(Screen):
    name = "Text"

    def __init__(self, font_path: str, message: str):
        self.font = graphics.Font()
        self.font.LoadFont(font_path)
        self.message = message

        self.palette = [
            graphics.Color(255, 255, 255),  # white
            graphics.Color(255, 0, 0),      # red
            graphics.Color(0, 255, 0),      # green
            graphics.Color(0, 0, 255),      # blue
            graphics.Color(255, 255, 0),    # yellow
            graphics.Color(255, 0, 255),    # magenta
            graphics.Color(0, 255, 255),    # cyan
        ]
        self.color_i = 0

        # Optional: an edit mode (not required). If you want rotate to adjust color ONLY in edit mode.
        self.edit_mode = False

    def handle(self, event: dict) -> bool:
        et = event.get("type")

        # Short click: change color once (your request)
        if et == "SHORT_CLICK":
            self.color_i = (self.color_i + 1) % len(self.palette)
            return True

        # Long click: reset color (or toggle edit mode if you prefer)
        if et == "LONG_CLICK":
            # Option A: reset
            self.color_i = 0
            return True

            # Option B (instead): toggle edit mode
            # self.edit_mode = not self.edit_mode
            # return True

        # If you want rotation to change color only when in edit mode, enable this:
        if self.edit_mode and et == "ROTATE":
            d = event.get("delta", 0)
            self.color_i = (self.color_i + (1 if d > 0 else -1)) % len(self.palette)
            return True

        return False

    def draw(self, canvas):
        canvas.Clear()
        color = self.palette[self.color_i]
        graphics.DrawText(canvas, self.font, 2, 12, color, self.message)

        # If edit_mode is enabled, draw a small marker (optional)
        if self.edit_mode:
            # tiny marker at top-left
            canvas.SetPixel(0, 0, 255, 255, 255)
