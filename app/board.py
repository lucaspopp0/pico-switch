from machine import Pin, PWM, Timer
import time
import asyncio
import errno

from . import request, config, update_manager
from .neopixels import NeoPixels

longpress_ms = 1500
update_longpress_ms = 5000
ble_longpress_ms = 5000

is_setup = False

request_queue = request.RequestQueue()

accepting_inputs = False
preparing_update = False
preparing_pairing = False


def _set_wifi_connected(connected):
    pass


set_wifi_connected = _set_wifi_connected


def pwmFreq(perc):
    return int((perc / 100.0) * 65_535.0)


def _buttonAction(key, long=False, flash_progress=True):
    global accepting_inputs, shared

    def act():
        deadline_passed = False
        request_complete = False

        def pass_deadline(_):
            deadline_passed = True

            if request_complete and flash_progress and shared is not None:
                shared.do_color(0, 0, 0)

        deadline_timer = Timer().init(mode=Timer.ONE_SHOT,
                                      period=1000,
                                      callback=pass_deadline)

        if not accepting_inputs:
            print("Ignoring press of " + str(key) +
                  ", not accepting inputs right now")
            return

        # Set up a new request
        encoded_name = request.urlencode(config.value["name"])
        request_path = 'remote-press?remote=' + encoded_name + '&button=' + str(
            key)
        req = request.Request(request_path)

        # Setup the success callback
        def on_success(_):
            request_complete = True
            if deadline_passed and flash_progress and shared is not None:
                shared.do_color(0, 0, 0)

        req.on_success = on_success

        # Setup the failure callback
        def on_failure(_):
            request_complete = True
            if shared is not None:
                asyncio.run(shared.flash(50, 0, 0, times=2))

        req.on_failure = on_failure

        # Flash LED on send
        if flash_progress and shared is not None:
            if long:
                shared.do_color(0, 15, 15)
            else:
                shared.do_color(15, 15, 15)

        print('Sending: ' + str(key))

        try:
            # Send the request
            req.send(request_queue)
        except OSError as oserr:
            print("Failed to send: " + str(oserr))

            # Run the failure callback if sending failed
            req.failed()

            if oserr.args[0] == errno.EHOSTUNREACH:
                set_wifi_connected(False)

    return act


class Button:

    def __init__(self, pins, key, board, override_action=None):
        self.board = board
        self.pins = pins
        self.gpios = list(map(lambda pin: Pin(pin, Pin.IN, Pin.PULL_UP), pins))
        self.last_pressed = False
        self.pressed = False
        self.last_press_time = time.ticks_ms()
        self.longPressTimer = Timer()
        self.key = key

        if override_action is None:
            self.action = _buttonAction(key)
            self.long = _buttonAction(str(key) + '-long', long=True)
        else:
            self.action = override_action(key)
            self.long = override_action(str(key) + '-long', long=True)

        def _action(p):
            self._action()

        for gpio in self.gpios:
            gpio.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=_action)

    def update(self):
        self._action()

    def _action(self):
        self.last_pressed = self.pressed
        # check equal to zero due to using PULL_UP resistor
        self.pressed = any(pin.value() == 0 for pin in self.gpios)

        if self.pressed != self.last_pressed:
            if self.pressed:
                self.board._button_press(self)

                def lpc(t):
                    self._long_action()

                self.longPressTimer.init(mode=Timer.ONE_SHOT,
                                         period=longpress_ms,
                                         callback=lpc)

                now = time.ticks_ms()
                self.last_press_time = now
                self.action()
            else:
                self.board._button_unpress(self)
                self._long_action()

    def _long_action(self):
        if self.long != None and self.pressed:
            self.long()


class RgbLed:

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
        self.r.duty_u16(pwmFreq(0))
        self.g.duty_u16(pwmFreq(0))
        self.b.duty_u16(pwmFreq(0))

    def do_color(self, r, g, b):
        self.r.duty_u16(pwmFreq(r))
        self.g.duty_u16(pwmFreq(g))
        self.b.duty_u16(pwmFreq(b))

    async def flash(self, r, g, b, seconds=0.1, times=1):
        for x in range(times):
            self.do_color(r, g, b)
            time.sleep(seconds)
            self.off()
            time.sleep(seconds)


class Routine:

    def __init__(self, name, color, button):
        self.name = name
        self.color = color
        self.button = button


class Wheel:

    def __init__(self, led, clk, dt, sw, handle_press, options):
        self.led = led
        self.handle_press = handle_press
        self.clk = Pin(clk, Pin.IN)
        self.dt = Pin(dt, Pin.IN)
        self.sw = Pin(sw, Pin.IN, Pin.PULL_UP)
        self.options = options
        self.enabled = True

        self.currentA = 0
        self.lastA = 0
        self.size = len(options)
        self.value = 0

        self.last_pressed = False
        self.pressed = False
        self.longPressTimer = Timer()

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

        self.timer = Timer(mode=Timer.ONE_SHOT,
                           period=1000,
                           callback=lambda t: self._led_off())

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

                self.longPressTimer.init(mode=Timer.ONE_SHOT,
                                         period=longpress_ms,
                                         callback=lpc)
                self._send_hook()

    def _long_action(self):
        if self.pressed:
            self._send_hook(True)

    def _send_hook(self, long=False):
        if self.timer is not None:
            self.timer.deinit()

        self._flash_color()

        name = self.current_option().name
        if long:
            name = name + '-long'

        self.handle_press(name, long, flash_progress=False)()
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


class V2Button:

    def __init__(self, buttonPin, neopixels: NeoPixels, key, board):
        # Fill in the configuration
        self.buttonPin = buttonPin
        self.neopixels = neopixels
        self.key = key
        self.board = board

        self.color = (255, 0, 0)
        self.pressTimer = Timer()

        # Set up the button and neopixels
        def press_callback(_, long=False):
            return self.on_press(long)

        self.button = Button([self.buttonPin], self.key, self.board,
                             press_callback)

        self.request_done = False
        self.timeout_done = False

    def on_press(self, long=False):
        global accepting_inputs, shared
        accepting_inputs = False

        self.request_done = False
        self.timeout_done = False

        key = str(self.key)
        if long:
            key += '-long'

        def off():
            if self.key == 'off':
                self.neopixels.set_button(self.key, (3, 1, 0))
            else:
                self.neopixels.set_button(self.key, (0, 0, 0))

        def on_success(response):
            self.request_done = True
            if self.timeout_done:
                off()

        def on_failure(response):
            self.request_done = True
            self.neopixels.set_button(self.key, (30, 0, 0))
            time.sleep(2)
            off()

        def press_timeout(t):
            self.timeout_done = True
            if self.request_done:
                off()

        req = request.Request('remote-press?remote=' +
                              request.urlencode(config.value["name"]) +
                              '&button=' + key)
        req.on_success = on_success
        req.on_failure = on_failure

        def act():
            global accepting_inputs

            if not accepting_inputs:
                print("Ignoring press of " + str(self.key) +
                      ", not accepting inputs right now")

            self.pressTimer.deinit()

            self.neopixels.set_button('off', (3, 1, 0))

            if long:
                self.neopixels.set_button(self.key, (0, 15, 15))
            else:
                self.neopixels.set_button(self.key, (10, 10, 10))

            self.pressTimer.init(mode=Timer.ONE_SHOT,
                                 period=1000,
                                 callback=press_timeout)

            print('Sending: ' + str(self.key))

            try:
                req.send(request_queue)
            except OSError as oserr:
                print("Failed to send: " + str(oserr))

                req.failed()

                if oserr.args[0] == errno.EHOSTUNREACH:
                    set_wifi_connected(False)

        return act


class Board:

    def __init__(self, layout):
        self.layout = layout
        self.buttons = None
        self.led = None
        self.dial = None
        self.switch = None
        self.neopixels = None

        self._pressed = {}
        self._update_press_timer = Timer()
        self._ble_press_timer = Timer()

        self._should_update = False
        self._should_pair = False
        self.needs_pairing = False

        if layout == "v4":
            self.led = RgbLed(16, 17, 18)
            self.buttons = {
                "on": Button([9, 6], 'on', self),
                "off": Button([3, 2], 'off', self),
                "1": Button([10], 1, self),
                "2": Button([11], 2, self),
                "3": Button([8], 3, self),
                "4": Button([7], 4, self),
                "5": Button([5], 5, self),
                "6": Button([4], 6, self),
                "7": Button([1], 8, self),
                "8": Button([0], 7, self),
            }
        elif layout == "v3":
            self.led = RgbLed(18, 17, 16)
            self.buttons = {
                "on": Button([0, 5], 'on', self),
                "off": Button([10, 15], 'off', self),
                "1": Button([28], 1, self),
                "2": Button([11], 2, self),
                "3": Button([6], 3, self),
                "4": Button([1], 4, self),
                "5": Button([27], 5, self),
                "6": Button([12], 6, self),
                "7": Button([7], 7, self),
                "8": Button([2], 8, self),
                "9": Button([26], 9, self),
                "10": Button([13], 10, self),
                "11": Button([8], 11, self),
                "12": Button([3], 12, self),
            }
        elif layout == "v5":
            self.led = RgbLed(16, 17, 18)

            dialScenes = []

            if config.value["wheel-routines"]:
                for routine in config.value["wheel-routines"]:
                    scene = Routine(routine["name"], routine["rgb"], 0)
                    dialScenes.append(scene)

            self.dial = Wheel(self.led, 7, 6, 8, _buttonAction, dialScenes)
            self.buttons = {
                "on": Button([13, 14], 'on', self),
                "off": Button([0, 2], 'off', self),
                "5": Button([15], 5, self),
                "6": Button([12], 6, self),
                "7": Button([11], 7, self),
                "8": Button([1], 8, self),
            }
        elif layout == "v6":
            self.led = RgbLed(16, 17, 18)

            dialScenes = []

            if config.value["wheel-routines"]:
                for routine in config.value["wheel-routines"]:
                    scene = Routine(routine["name"], routine["rgb"], 0)
                    dialScenes.append(scene)

            self.dial = Wheel(self.led, 7, 6, 8, _buttonAction, dialScenes)
            self.buttons = {
                "on": Button([13, 14], 'on', self),
                "off": Button([0, 2], 'off', self),
                "5": Button([15], 5, self),
                "6": Button([12], 6, self),
                "7": Button([11], 7, self),
                "8": Button([1], 8, self),
            }

            def _on():
                global accepting_inputs, dial
                print("Accepting inputs")
                accepting_inputs = True
                if self.dial is not None:
                    self.dial.enabled = True

            def _off():
                global accepting_inputs, dial
                print("Not accepting inputs")
                accepting_inputs = False
                if dial is not None:
                    dial.enabled = False

            self.switch = Switch(27, 28, {"on": _on, "off": _off})

        elif layout == "v7":
            self.led = RgbLed(18, 19, 20)

            self.buttons = {
                "on": Button([10, 9], 'on', self),
                "off": Button([5, 4], 'off', self),
                "1": Button([12], 1, self),
                "2": Button([11], 2, self),
                "3": Button([7], 3, self),
                "4": Button([8], 4, self),
                "5": Button([0], 5, self),
                "6": Button([3], 6, self),
                "7": Button([1], 7, self),
                "8": Button([2], 8, self),
            }

        elif layout == "v8":
            self.neopixels = NeoPixels()
            self.buttons = {
                "on": V2Button(3, self.neopixels, "on", self),
                "off": V2Button(19, self.neopixels, "off", self),
                #"1": V2Button(1, self.neopixels, "1", self),
                "2": V2Button(2, self.neopixels, "2", self),
                "3": V2Button(5, self.neopixels, "3", self),
                "4": V2Button(6, self.neopixels, "4", self),
                #"5": V2Button(17, self.neopixels, "5", self),
                "6": V2Button(18, self.neopixels, "6", self),
                "7": V2Button(21, self.neopixels, "7", self),
                "8": V2Button(22, self.neopixels, "8", self),
            }
        else:
            print("Unexpected config layout: " + str(layout))

    def _button_press(self, button):
        global accepting_inputs, preparing_update, preparing_pairing

        print("Pressed " + str(button.key))

        self._pressed[str(button.key)] = True

        self._should_update = self._could_update()
        if self._should_update:
            self._should_pair = False
            accepting_inputs = False
            preparing_update = True

            print("Update press detected")

            def upc(_):
                self._try_update()

            self._update_press_timer.deinit()
            self._update_press_timer.init(mode=Timer.ONE_SHOT,
                                          period=update_longpress_ms,
                                          callback=upc)

        else:
            self._should_pair = self._could_pair()

            if self._should_pair:
                print("Pairing press detected")

                preparing_pairing = True
                accepting_inputs = False

                def ble_trigger(_):
                    if self._should_pair:
                        self.needs_pairing = True

                self._ble_press_timer.deinit()
                self._ble_press_timer.init(mode=Timer.ONE_SHOT,
                                           period=ble_longpress_ms,
                                           callback=ble_trigger)

    def _button_unpress(self, button):
        global accepting_inputs, preparing_update, preparing_pairing

        if str(button.key) in self._pressed:
            del self._pressed[str(button.key)]

        self._should_update = self._could_update()
        if preparing_update and not self._should_update:
            accepting_inputs = True
            preparing_update = False
            self._update_press_timer.deinit()

        self._should_pair = self._could_pair()
        if preparing_pairing and not self.needs_pairing and not self._should_pair:
            preparing_pairing = False
            accepting_inputs = True
            self._ble_press_timer.deinit()

    def _could_pair(self):
        return len(self._pressed) == 2

    def _could_update(self):
        return len(self._pressed) == 4

    def _try_update(self):
        if self._could_update():
            print("Checking for updates...")
            update_manager.try_update()

    def do_color(self, r, g, b):
        if self.neopixels is not None:
            self.neopixels.set_all((r, g, b))
        elif self.led is not None:
            self.led.do_color(r, g, b)

    async def flash(self, r, g, b, seconds=0.1, times=1):
        if self.neopixels is not None:
            return self.neopixels.flash((r, g, b),
                                        seconds=seconds,
                                        times=times)
        elif self.led is not None:
            return self.led.flash(r, g, b, seconds=seconds, times=times)


shared: Board | None = None


def setup():
    global led, is_setup, dial, switch, accepting_inputs, shared

    if is_setup:
        return
    is_setup = True

    shared = Board(config.value["layout"])
