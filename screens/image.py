from rgbmatrix import graphics
from PIL import Image, ImageOps
from .base import Screen


class ImageScreen(Screen):
    name = "Image"

    def __init__(self, image_paths, size=(64, 32), nearest=True):
        """
        image_paths: list[str] or a single str
        size: (width, height) expected by your panel, e.g. (64, 32)
        nearest: True uses pixel-art friendly scaling
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        self.image_paths = image_paths
        self.size = size
        self.nearest = nearest

        self.index = 0
        self.invert = False  # optional effect
        self._cache = {}     # cache loaded/resized images
        self.edit_mode = false
        # Optional text overlay (if you want)
        self.font = graphics.Font()
        # load a font only if you want overlay text:
        # self.font.LoadFont("/home/admin/rpi-rgb-led-matrix/fonts/6x10.bdf")

    def _load_image(self, path: str) -> Image.Image:
        """Load + resize + convert to RGB. Cached."""
        key = (path, self.size, self.nearest)
        if key in self._cache:
            return self._cache[key]

        img = Image.open(path).convert("RGB")
        resample = Image.NEAREST if self.nearest else Image.BICUBIC
        img = img.resize(self.size, resample=resample)

        self._cache[key] = img
        return img

    def handle(self, event: dict) -> bool:
        et = event.get("type")

        # Toggle edit mode
        if et == "SHORT_CLICK":
            self.edit_mode = not self.edit_mode
            return True

        # Long click could invert, reset, etc.
        if et == "LONG_CLICK":
            self.invert = not self.invert
            return True

        # Only consume ROTATE when in edit mode
        if et == "ROTATE" and self.edit_mode:
            d = event.get("delta", 0)
            if d > 0:
                self.index = (self.index + 1) % len(self.image_paths)
            elif d < 0:
                self.index = (self.index - 1) % len(self.image_paths)
            return True

        # Otherwise, do NOT handle rotate — let manager switch screens
        return False


    def draw(self, canvas):
        canvas.Clear()

        path = self.image_paths[self.index]
        img = self._load_image(path)

        if self.invert:
            img_to_show = ImageOps.invert(img)
        else:
            img_to_show = img

        # Draw full image at (0,0)
        canvas.SetImage(img_to_show, 0, 0)

        # Optional overlay text:
        # white = graphics.Color(255, 255, 255)
        # graphics.DrawText(canvas, self.font, 1, 31, white, f"{self.index+1}/{len(self.image_paths)}")
