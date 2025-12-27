from rgbmatrix import RGBMatrix, RGBMatrixOptions


class MatrixDisplay:
    """
    Wraps hzeller RGBMatrix options in one place.
    """

    def __init__(
        self,
        *,
        cols=64,
        rows=32,
        chain_length=1,
        parallel=1,
        brightness=60,
        gpio_mapping="adafruit-hat",
        panel_type=None,          # e.g. "FM6126A" if needed
        slowdown_gpio=4,
        pwm_bits=None,
        pwm_lsb_nanoseconds=None,
    ):
        opts = RGBMatrixOptions()
        opts.cols = cols
        opts.rows = rows
        opts.chain_length = chain_length
        opts.parallel = parallel
        opts.brightness = brightness
        opts.hardware_mapping = gpio_mapping
        opts.gpio_slowdown = slowdown_gpio

        if panel_type:
            opts.panel_type = panel_type
        if pwm_bits is not None:
            opts.pwm_bits = pwm_bits
        if pwm_lsb_nanoseconds is not None:
            opts.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds

        self.matrix = RGBMatrix(options=opts)

    def create_canvas(self):
        return self.matrix.CreateFrameCanvas()

    def swap(self, canvas):
        return self.matrix.SwapOnVSync(canvas)
