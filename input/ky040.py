import time
import threading


class KY040Input:
    """
    Polling-based KY-040 input:
      ROTATE:      {"type":"ROTATE","delta":+1/-1}
      SHORT_CLICK: {"type":"SHORT_CLICK"}
      LONG_CLICK:  {"type":"LONG_CLICK"}

    Key improvement vs your version:
    - Proper quadrature decode (CLK/DT) so slow turns register.
    - Emits exactly 1 ROTATE per detent via steps_per_detent.
    """

    def __init__(
        self,
        gpio,
        clk_pin: int,
        dt_pin: int,
        sw_pin: int,
        out_queue,
        *,
        pull_up=True,
        long_press_s: float = 0.60,
        debounce_s: float = 0.03,
        poll_s: float = 0.0005,          # poll faster for encoders
        invert_direction: bool = False,
        steps_per_detent: int = 1,        # TRY 2 first; if too sensitive, use 4; if too sluggish, use 1
        rot_debounce_s: float = 0.0005,   # minimum time between valid quad steps
    ):
        self.gpio = gpio
        self.clk = clk_pin
        self.dt = dt_pin
        self.sw = sw_pin
        self.q = out_queue

        self.pull_up = pull_up
        self.long_press_s = long_press_s
        self.debounce_s = debounce_s
        self.poll_s = poll_s
        self.invert_direction = invert_direction
        self.steps_per_detent = max(1, int(steps_per_detent))
        self.rot_debounce_s = rot_debounce_s

        self._stop = threading.Event()
        self._thread = None

        # rotation state
        self._last_state = 0
        self._accum = 0
        self._last_rot_time = 0.0

        # button state
        self._pressed = False
        self._press_time = 0.0
        self._last_btn_edge = 0.0
        self._prev_sw = 1  # pull-up idle HIGH

    def start(self):
        g = self.gpio
        g.setmode(g.BCM)

        pud = g.PUD_UP if self.pull_up else g.PUD_DOWN
        g.setup(self.clk, g.IN, pull_up_down=pud)
        g.setup(self.dt,  g.IN, pull_up_down=pud)
        g.setup(self.sw,  g.IN, pull_up_down=pud)

        if hasattr(g, "set_glitch_filter"):
            g.set_glitch_filter(self.clk, 800)   # 0.8ms
            g.set_glitch_filter(self.dt,  800)
            g.set_glitch_filter(self.sw, 3000)   # 3ms for button

        # initial states
        self._last_state = (g.input(self.clk) << 1) | g.input(self.dt)
        self._prev_sw = g.input(self.sw)

        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _emit_rotate(self, delta: int):
        if self.invert_direction:
            delta = -delta
        print("DEBUG ROTATE", delta)
        self.q.put({"type": "ROTATE", "delta": delta})

    def _emit_short(self):
        print("DEBUG SHORT")
        self.q.put({"type": "SHORT_CLICK"})

    def _emit_long(self):
        print("DEBUG LONG")
        self.q.put({"type": "LONG_CLICK"})

    def _run(self):
        g = self.gpio

        # Quadrature transition table
        # state is 2-bit: (CLK<<1)|DT
        TRANS = {
            (0b00, 0b01): +1,
            (0b01, 0b11): +1,
            (0b11, 0b10): +1,
            (0b10, 0b00): +1,

            (0b00, 0b10): -1,
            (0b10, 0b11): -1,
            (0b11, 0b01): -1,
            (0b01, 0b00): -1,
        }

        while not self._stop.is_set():
            now = time.monotonic()

            # ---------- ROTATION ----------
            state = (g.input(self.clk) << 1) | g.input(self.dt)
            if state != self._last_state:
                step = TRANS.get((self._last_state, state), 0)
                self._last_state = state

                # Filter out super-fast bounce steps
                if step != 0 and (now - self._last_rot_time) >= self.rot_debounce_s:
                    self._last_rot_time = now
                    self._accum += step

                    # Emit one event per detent
                    if self._accum >= self.steps_per_detent:
                        self._accum = 0
                        self._emit_rotate(+1)
                    elif self._accum <= -self.steps_per_detent:
                        self._accum = 0
                        self._emit_rotate(-1)

            # ---------- BUTTON (SHORT vs LONG) ----------
            sw_state = g.input(self.sw)

            if sw_state != self._prev_sw and (now - self._last_btn_edge) > self.debounce_s:
                self._last_btn_edge = now

                if sw_state == 0 and not self._pressed:
                    self._pressed = True
                    self._press_time = now

                elif sw_state == 1 and self._pressed:
                    self._pressed = False
                    held = now - self._press_time
                    if held >= self.long_press_s:
                        self._emit_long()
                    else:
                        self._emit_short()

            self._prev_sw = sw_state

            time.sleep(self.poll_s)
