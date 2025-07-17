from machine import Pin, Timer
from .basics import PushButton


class Routine:

    def __init__(self, name, color, button):
        self.name = name
        self.color = color
        self.button = button


class Wheel:

    def __init__(self, led, clk, dt, sw, options):
        self.led = led
        self.clk = Pin(clk, Pin.IN)
        self.dt = Pin(dt, Pin.IN)
        self.sw = Pin(sw, Pin.IN, Pin.PULL_UP)
        self.options = options
        self.enabled = True

        self.currentA = 0
        self.lastA = 0
        self.size = len(options)
        self.value = 0

        self.on_press = lambda routine: None
        self.on_long_press = lambda routine: None

        self.last_pressed = False
        self.pressed = False
        self.longPressTimer: Timer | None = None

        self.clk.irq(lambda p: self._rotated())
        self.sw.irq(lambda p: self._pressed())

        self.timer = None
        self._flash_color()
        self._reset_timer()

    def current_option(self):
        return self.options[self.value]

    def _led_off(self):
        self.led.off()

    def _reset_timer(self):
        if self.timer != None:
            self.timer.deinit()
            self.timer = None

        self.timer = Timer(-1, mode=Timer.ONE_SHOT, period=1000, callback=lambda t: self._led_off())


    def _rotated(self):
        a = self.clk.value()
        b = self.dt.value()

        self.lastA = self.currentA
        self.currentA = a

        if a == 0:
            return

        if not self.enabled:
            print("Not enabled")
            return

        if self.currentA == self.lastA:
            return

        if a == b:
            self.value = self.value + 1
        else:
            self.value = self.value - 1

        self.value = self.value % self.size

        print("scrolled to: " + self.options[self.value].name)

        self._flash_color()
        self._reset_timer()

    def _pressed(self):
        self.last_pressed = self.pressed
        # check equal to zero due to using PULL_UP resistor
        self.pressed = self.sw.value() == 0

        if self.pressed != self.last_pressed:
            if self.pressed:
                print("pressed: " + self.current_option().name)

                def lpc(t):
                    self._long_action()

                self.longPressTimer = Timer(-1, mode=Timer.ONE_SHOT, period=PushButton.longpress_ms, callback=lpc)
                self._send_hook()

    def _long_action(self):
        if self.pressed:
            self._send_hook(True)

    def _send_hook(self, long=False):
        if self.timer is not None:
            self.timer.deinit()
            
        self._flash_color()

        if long:
            self.on_long_press(self.current_option())
        else:
            self.on_press(self.current_option())

        self._reset_timer()

    def _flash_color(self):
        color = self.current_option().color
        self.led.do_color(color[0], color[1], color[2])


class Switch:

    def __init__(self, powerPin, switchPin, callbacks):
        self.powerPin = Pin(powerPin, Pin.OUT)
        self.switchPin = Pin(switchPin, Pin.IN)
        self.callbacks = callbacks

        self.powerPin.value(1)

        def _callback(pin):
            self.callback(pin.value())

        self.switchPin.irq(_callback)

    def callback(self, value):
        if value:
            self.callbacks["on"]()
        else:
            self.callbacks["off"]()
