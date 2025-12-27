import time
import threading


class KY040Input:
    """
    Reads a KY-040 rotary encoder (CLK/DT) + pushbutton (SW)
    and emits events into a queue:

      ROTATE:      {"type":"ROTATE","delta":+1/-1}
      SHORT_CLICK: {"type":"SHORT_CLICK"}
      LONG_CLICK:  {"type":"LONG_CLICK"}

    Notes:
    - Uses polling in a background thread (simple + reliable).
    - Button press type is decided on RELEASE to avoid "short then long" double-firing.
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
        poll_s: float = 0.001,
        invert_direction: bool = False,
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

        self._stop = threading.Event()
        self._thread = None

        # encoder state
        self._last_clk = None

        # button state
        self._pressed = False
        self._press_time = 0.0
        self._last_edge = 0.0
        self._prev_sw = 1  # pull-up idle HIGH

    def start(self):
        g = self.gpio
        g.setmode(g.BCM)

        pud = g.PUD_UP if self.pull_up else g.PUD_DOWN
        g.setup(self.clk, g.IN, pull_up_down=pud)
        g.setup(self.dt,  g.IN, pull_up_down=pud)
        g.setup(self.sw,  g.IN, pull_up_down=pud)

        self._last_clk = g.input(self.clk)
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
        self.q.put({"type": "ROTATE", "delta": delta})

    def _emit_short(self):
        self.q.put({"type": "SHORT_CLICK"})

    def _emit_long(self):
        self.q.put({"type": "LONG_CLICK"})

    def _run(self):
        g = self.gpio

        while not self._stop.is_set():
            now = time.monotonic()

            # ---------- ROTATION ----------
            clk_state = g.input(self.clk)
            dt_state = g.input(self.dt)

            # Detect rising edge on CLK
            if clk_state != self._last_clk and clk_state == 1:
                # Direction heuristic:
                # Often: dt == 0 => CW, dt == 1 => CCW (may vary by wiring)
                delta = +1 if dt_state == 0 else -1
                self._emit_rotate(delta)

            self._last_clk = clk_state

            # ---------- BUTTON (SHORT vs LONG) ----------
            sw_state = g.input(self.sw)

            # Edge detect with debounce
            if sw_state != self._prev_sw and (now - self._last_edge) > self.debounce_s:
                self._last_edge = now

                if sw_state == 0 and not self._pressed:
                    # PRESS
                    self._pressed = True
                    self._press_time = now

                elif sw_state == 1 and self._pressed:
                    # RELEASE
                    self._pressed = False
                    held = now - self._press_time
                    if held >= self.long_press_s:
                        self._emit_long()
                    else:
                        self._emit_short()

            self._prev_sw = sw_state

            time.sleep(self.poll_s)
