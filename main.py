import time
import queue
from input.gpio_pigpio import PigpioGPIO
GPIO = PigpioGPIO()

from input import KY040Input
from display import MatrixDisplay
from manager import ScreenManager
from screens import ClockScreen, TextScreen


def main():
    # -------- CONFIG YOU SHOULD EDIT --------
    FONT_PATH = "/home/admin/rpi-rgb-led-matrix/fonts/6x10.bdf"

    # KY-040 pins (BCM numbering)
    # Change these to your wiring
    CLK_PIN = 18
    DT_PIN  = 19 
    SW_PIN  = 25

    # Matrix options (tune to your setup)
    MATRIX_COLS = 64
    MATRIX_ROWS = 32
    BRIGHTNESS = 60
    GPIO_MAPPING = "adafruit-hat"
    PANEL_TYPE = "FM6126A"  
    SLOWDOWN = 4
    # ---------------------------------------

    events = queue.Queue()

    display = MatrixDisplay(
        cols=MATRIX_COLS,
        rows=MATRIX_ROWS,
        brightness=BRIGHTNESS,
        gpio_mapping=GPIO_MAPPING,
        panel_type=PANEL_TYPE,
        slowdown_gpio=SLOWDOWN,
    )

    screens = [
        ClockScreen(FONT_PATH),
        TextScreen(FONT_PATH, "Salaam!"),
    ]
    mgr = ScreenManager(screens)

    encoder = KY040Input(
        gpio=GPIO,
        clk_pin=CLK_PIN,
        dt_pin=DT_PIN,
        sw_pin=SW_PIN,
        out_queue=events,
        long_press_s=0.60,
        debounce_s=0.03,
        poll_s=0.001,
        invert_direction=False,  # set True if rotation direction feels backwards
    )
    #encoder.start()

    canvas = display.create_canvas()
    last = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last
            last = now

            # 1) handle all pending input events
            while True:
                try:
                    ev = events.get_nowait()
                    print(ev)
                    mgr.handle(ev)
                except queue.Empty:
                    break
                mgr.handle(ev)

            # 2) update time-based state
            mgr.current.update(dt)

            # 3) draw current screen
            mgr.current.draw(canvas)
            canvas = display.swap(canvas)

            # ~60 FPS cap
            time.sleep(1 / 60)
    finally:
        #encoder.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
