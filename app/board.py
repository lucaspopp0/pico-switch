from machine import Pin, PWM, Timer
import time
import uasyncio
from . import request
from . import config
from . import wheel
from .switch import Switch
from . import constants

is_setup = False

request_queue = request.RequestQueue()

led = None

dial = None

switch = None

accepting_inputs = True

def pwmFreq(perc):
    return int((perc / 100.0) * 65_535.0)

def _buttonAction(key, long=False, flash_progress=True):
    global accepting_inputs

    req = request.Request('remote-press?remote=' + request.urlencode(config.value["name"]) + '&button=' + str(key))
    def on_success(response):
        if flash_progress:
            led.off()
    def on_failure(response):
        uasyncio.run(led.flash(100, 0, 0, times=2))
    req.on_success = on_success
    req.on_failure = on_failure
    def act():
        global accepting_inputs

        if not accepting_inputs:
            print("Remote off")
            return

        if flash_progress:
            if long:
                led.do_color(0, 50, 50)
            else:
                led.do_color(0, 0, 50)

        print('Sending: ' + str(key))

        try:
            req.send(request_queue)
        except OSError as e:
            print("Failed to send: " + str(e))
            req.failed()

    return act

class Button:

    def __init__(self, pins, key):
        self.pins = pins
        self.gpios = list(map(lambda pin : Pin(pin, Pin.IN, Pin.PULL_UP), pins))
        self.last_pressed = False
        self.pressed = False
        self.last_press_time = time.ticks_ms()
        self.longPressTimer = Timer()

        self.action = _buttonAction(key)
        self.long = _buttonAction(str(key) + '-long', long=True)

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
                def lpc(t):
                    self._long_action()

                self.longPressTimer.init(mode=Timer.ONE_SHOT, period=constants.longpress_ms, callback=lpc)
                now = time.ticks_ms()
                self.last_press_time = now
                self.action()
            else:
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

    async def flash(self, r, g, b, seconds = 0.1, times = 1):
        for x in range(times):
            self.do_color(r, g, b)
            time.sleep(seconds)
            self.off()
            time.sleep(seconds)

def keypress(num):
    req = request.Request('remote-press?remote=' + request.urlencode('New Bedroom') + '&button=' + str(num))

    def inner():
        print("sending")
        req.send(request_queue)

    return inner

def longpress(num):
    return keypress(str(num) + "-long")

def setup():
    global led, is_setup, dial, switch, accepting_inputs
    if is_setup:
        return
    is_setup = True
    if config.value["layout"] == "v4":
        led = RgbLed(16, 17, 18)
        buttonON = Button([9, 6], 'on')
        buttonOFF = Button([3, 2], 'off')
        button1 = Button([10], 1)
        button2 = Button([11], 2)
        button3 = Button([8], 3)
        button4 = Button([7], 4)
        button5 = Button([5], 5)
        button6 = Button([4], 6)
        button7 = Button([1], 7)
        button8 = Button([0], 8)
    elif config.value["layout"] == "v3":
        led = RgbLed(18, 17, 16)
        buttonON = Button([0, 5], 'on')
        buttonOFF = Button([10, 15], 'off')
        button1 = Button([28], 1)
        button2 = Button([11], 2)
        button3 = Button([6], 3)
        button4 = Button([1], 4)
        button5 = Button([27], 5)
        button6 = Button([12], 6)
        button7 = Button([7], 7)
        button8 = Button([2], 8)
        button9 = Button([26], 9)
        button10 = Button([13], 10)
        button11 = Button([8], 11)
        button12 = Button([3], 12)
    elif config.value["layout"] == "v5":
        led = RgbLed(16, 17, 18)

        dialScenes = []

        if config.value["wheel-routines"]:
            for routine in config.value["wheel-routines"]:
                scene = wheel.Routine(routine["name"], routine["rgb"], 0)
                dialScenes.append(scene)

        dial = wheel.Wheel(led, 7, 6, 8, _buttonAction, dialScenes)
        buttonON = Button([13, 14], 'on')
        buttonOFF = Button([0, 2], 'off')
        button1 = Button([15], 5)
        button2 = Button([12], 6)
        button3 = Button([11], 7)
        button4 = Button([1], 8)
    elif config.value["layout"] == "v6":
        led = RgbLed(16, 17, 18)

        dialScenes = []

        if config.value["wheel-routines"]:
            for routine in config.value["wheel-routines"]:
                scene = wheel.Routine(routine["name"], routine["rgb"], 0)
                dialScenes.append(scene)

        dial = wheel.Wheel(led, 7, 6, 8, _buttonAction, dialScenes)
        buttonON = Button([13, 14], 'on')
        buttonOFF = Button([0, 2], 'off')
        button1 = Button([15], 5)
        button2 = Button([12], 6)
        button3 = Button([11], 7)
        button4 = Button([1], 8)

        def _on():
            global accepting_inputs, dial
            print("Accepting inputs")
            accepting_inputs = True
            if dial is not None:
                dial.enabled = True

        def _off():
            global accepting_inputs, dial
            print("Not accepting inputs")
            accepting_inputs = False
            if dial is not None:
                dial.enabled = False


        switch = Switch(27, 28, {
            "on": _on,
            "off": _off
        })

    else:
        print("Unexpected config layout: " + str(config.value["layout"]))
