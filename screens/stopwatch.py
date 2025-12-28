from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from rgbmatrix import graphics
from PIL import Image, ImageOps
from .base import Screen


@dataclass
class StopwatchState:
    mode: str = "idle"          # "idle" | "running" | "paused"
    elapsed_s: float = 0.0      # accumulated stopwatch time
    anim_i: int = 0             # current animation frame index
    anim_t: float = 0.0         # time accumulator for animation
    tick_t: float = 0.0         # time accumulator for display tick


class StopwatchScreen(Screen):
    name = "Stopwatch"

    def __init__(
        self,
        font_path: str,
        images_dir: str | Path,
        *,
        width: int = 64,
        height: int = 32,
        anim_fps: float = 12.0,          # animation speed
        display_fps: float = 30.0,       # how often we update the displayed time text
    ):
        self.w = width
        self.h = height

        self.font = graphics.Font()
        self.font.LoadFont(font_path)

        self.color = graphics.Color(0, 255, 255)   # cyan
        self.color2 = graphics.Color(255, 255, 255)

        self.images_dir = Path(images_dir)
        self.frames = self._load_frames(self.images_dir, self.w, self.h)

        self.anim_dt = 1.0 / max(anim_fps, 1.0)
        self.display_dt = 1.0 / max(display_fps, 1.0)

        self.s = StopwatchState()

        # cached render text (so we don't format every frame)
        self._time_text = "00:00.000"

    def _load_frames(self, images_dir: Path, w: int, h: int):
        frames = []
        for i in range(8):
            p = images_dir / f"stopwatch{i}.png"
            if not p.exists():
                raise FileNotFoundError(f"Missing animation frame: {p}")

            src = Image.open(p).convert("RGBA")

            # Use alpha as mask -> white foreground on black background
            alpha = src.split()[3]  # A channel

            # Make a white icon image the same size as src, masked by alpha
            icon = Image.new("RGB", src.size, (0, 0, 0))
            white = Image.new("RGB", src.size, (255, 255, 255))
            icon.paste(white, (0, 0), alpha)

            # Scale up (nearest keeps pixel-art crisp)
            # Choose a scale that fits inside 64x32 nicely
            # Example: target height 28px
            target_h = 25
            scale = max(1, target_h // src.size[1])
            new_w, new_h = src.size[0] * scale, src.size[1] * scale
            icon = icon.resize((new_w, new_h), Image.NEAREST)

            # Center on a 64x32 black frame
            frame = Image.new("RGB", (w, h), (0, 0, 0))
            x = (w - new_w) // 2
            y = (h - new_h) // 2
            frame.paste(icon, (x, y))

            frames.append(frame)

        return frames



    def _format_time(self, elapsed_s: float) -> str:
        total_ms = int(elapsed_s * 1000.0)
        if total_ms < 0:
            total_ms = 0
        ms = total_ms % 1000
        total_s = total_ms // 1000
        sec = total_s % 60
        minutes = (total_s // 60) % 100  # clamp display to 0..99 minutes
        return f"{minutes:02d}:{sec:02d}.{ms:03d}"

    def handle(self, event: dict) -> bool:
        et = event.get("type")

        if et == "LONG_CLICK":
            # reset to animation
            self.s = StopwatchState(mode="idle")
            self._time_text = "00:00.000"
            return True

        if et == "SHORT_CLICK":
            if self.s.mode == "idle":
                # start stopwatch from 0
                self.s.mode = "running"
                self.s.elapsed_s = 0.0
                self._time_text = "00:00.000"
                return True

            if self.s.mode == "running":
                self.s.mode = "paused"
                return True

            if self.s.mode == "paused":
                self.s.mode = "running"
                return True

        return False

    def update(self, dt: float):
        # ---------- idle animation ----------
        if self.s.mode == "idle":
            self.s.anim_t += dt
            while self.s.anim_t >= self.anim_dt:
                self.s.anim_t -= self.anim_dt
                self.s.anim_i = (self.s.anim_i + 1) % len(self.frames)
            return

        # ---------- stopwatch ----------
        if self.s.mode == "running":
            self.s.elapsed_s += dt

        # only refresh the formatted text at display_fps
        self.s.tick_t += dt
        if self.s.tick_t >= self.display_dt:
            self.s.tick_t %= self.display_dt
            self._time_text = self._format_time(self.s.elapsed_s)

    def draw(self, canvas):
        canvas.Clear()

        if self.s.mode == "idle":
            # draw animation frame
            canvas.SetImage(self.frames[self.s.anim_i], 0, 0)
            return

        # stopwatch display
        # Optional small label
        graphics.DrawText(canvas, self.font, 1, 10, self.color2,
                          "RUN" if self.s.mode == "running" else "PAUSE")
        graphics.DrawText(canvas, self.font, 1, 26, self.color, self._time_text)
