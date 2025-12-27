import pigpio

class PigpioGPIO:
    BCM = 0
    IN = 0
    PUD_UP = 2
    PUD_DOWN = 1

    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon not running. Run: sudo systemctl enable --now pigpiod")

    def setwarnings(self, flag: bool):
        pass  # not needed

    def setmode(self, mode):
        pass  # pigpio uses BCM numbering

    def setup(self, pin, direction, pull_up_down=None):
        self.pi.set_mode(pin, pigpio.INPUT)
        if pull_up_down == self.PUD_UP:
            self.pi.set_pull_up_down(pin, pigpio.PUD_UP)
        elif pull_up_down == self.PUD_DOWN:
            self.pi.set_pull_up_down(pin, pigpio.PUD_DOWN)
        else:
            self.pi.set_pull_up_down(pin, pigpio.PUD_OFF)

    def input(self, pin):
        return self.pi.read(pin)

    def cleanup(self):
        self.pi.stop()