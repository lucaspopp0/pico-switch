from machine import Pin, PWM, Timer
import time
import asyncio
import errno

# Configure a pushbutton using one or more pins using a PULL_UP mode
class PushButton:

    longpress_ms = 1500

    def __init__(self, pins, key):
        self.pins = pins
        self.key = key

        self.gpios = list(map(lambda pin : Pin(pin, Pin.IN, Pin.PULL_UP), pins))

        self.last_pressed = False
        self.pressed = False

        self.on_press = lambda : None
        self.on_long_press = lambda : None
        self.on_release = lambda : None

        self.long_press_timer = Timer()

    def _on_interrupt(self):
        self.last_pressed = self.pressed

        # Check equal to zero due to using PULL_UP
        self.pressed = any(pin.value() == 0 for pin in self.gpios)

        if self.pressed != self.last_pressed:
            self._on_change()

    def _on_change(self):
        if self.pressed:
            self.on_press()

            def longpress_callback(t):
                self.on_long_press()

            # Start a timer for a long press
            self.long_press_timer.init(
                mode=Timer.ONE_SHOT,
                period=PushButton.longpress_ms,
                callback=longpress_callback,
            )
        else:
            self.on_release()

class RgbLED:

    @staticmethod
    def pwmFreq(perc):
        return int((perc / 100.0) * 65_535.0)

    def __init__(self, rpin, gpin, bpin):
        self.rpin = Pin(rpin, Pin.OUT)
        self.gpin = Pin(gpin, Pin.OUT)
        self.bpin = Pin(bpin, Pin.OUT)

        self.r = PWM(self.rpin)
        self.g = PWM(self.gpin)
        self.b = PWM(self.bpin)

        self.r.freq(1_000)
        self.g.freq(1_000)
        self.b.freq(1_000)

    def off(self):
        self.r.duty_u16(RgbLED.pwmFreq(0))
        self.g.duty_u16(RgbLED.pwmFreq(0))
        self.b.duty_u16(RgbLED.pwmFreq(0))

    def do_color(self, r, g, b):
        self.r.duty_u16(RgbLED.pwmFreq(r))
        self.g.duty_u16(RgbLED.pwmFreq(g))
        self.b.duty_u16(RgbLED.pwmFreq(b))

    async def flash(self, r, g, b, seconds = 0.1, times = 1):
        for x in range(times):
            self.do_color(r, g, b)
            time.sleep(seconds)
            self.off()
            time.sleep(seconds)
