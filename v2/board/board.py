from machine import Timer
from .basics import PushButton, RgbLED
from .deprecated import Routine, Wheel, Switch

class Board:

    update_longpress_ms = 5000
    ble_longpress_ms = 5000

    def __init__(self, config):
        self.layout = config["layout"]
        self.buttons = None
        self.led = None
        self.dial = None
        self.switch = None
        self.accepting_inputs = False
        self.preparing_update = False
        self.preparing_pairing = False

        self._pressed = {}
        self._update_press_timer: Timer | None = None
        self._ble_press_timer: Timer | None = None
        
        self._should_update = False
        self._should_pair = False
        self.needs_pairing = False

        self.on_release = lambda : None
        self.on_update = lambda : None
        self.on_press = lambda key : None
        self.on_long_press = lambda key : None

        self.on_dial_press = lambda routine : None
        self.on_dial_long_press = lambda routine : None

        if self.layout == "v4":
            self.led = RgbLED(16, 17, 18)
            self.buttons = {
                "on": PushButton([9, 6], 'on'),
                "off": PushButton([3, 2], 'off'),
                "1": PushButton([10], 1),
                "2": PushButton([11], 2),
                "3": PushButton([8], 3),
                "4": PushButton([7], 4),
                "5": PushButton([5], 5),
                "6": PushButton([4], 6),
                "7": PushButton([1], 8),
                "8": PushButton([0], 7),
            }
        elif self.layout == "v3":
            self.led = RgbLED(18, 17, 16)
            self.buttons = {
                "on": PushButton([0, 5], 'on'),
                "off": PushButton([10, 15], 'off'),
                "1": PushButton([28], 1),
                "2": PushButton([11], 2),
                "3": PushButton([6], 3),
                "4": PushButton([1], 4),
                "5": PushButton([27], 5),
                "6": PushButton([12], 6),
                "7": PushButton([7], 7),
                "8": PushButton([2], 8),
                "9": PushButton([26], 9),
                "10": PushButton([13], 10),
                "11": PushButton([8], 11),
                "12": PushButton([3], 12),
            }
        elif self.layout == "v5":
            self.led = RgbLED(16, 17, 18)

            dialScenes = []

            if config["wheel-routines"]:
                for routine in config["wheel-routines"]:
                    scene = Routine(routine["name"], routine["rgb"], 0)
                    dialScenes.append(scene)

            self.dial = Wheel(self.led, 7, 6, 8, dialScenes)
            self.buttons = {
                "on": PushButton([13, 14], 'on'),
                "off": PushButton([0, 2], 'off'),
                "5": PushButton([15], 5),
                "6": PushButton([12], 6),
                "7": PushButton([11], 7),
                "8": PushButton([1], 8),
            }
        elif self.layout == "v6":
            self.led = RgbLED(16, 17, 18)

            dialScenes = []

            if config["wheel-routines"]:
                for routine in config["wheel-routines"]:
                    scene = Routine(routine["name"], routine["rgb"], 0)
                    dialScenes.append(scene)

            self.dial = Wheel(self.led, 7, 6, 8, dialScenes)
            self.buttons = {
                "on": PushButton([13, 14], 'on'),
                "off": PushButton([0, 2], 'off'),
                "5": PushButton([15], 5),
                "6": PushButton([12], 6),
                "7": PushButton([11], 7),
                "8": PushButton([1], 8),
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
                if self.dial is not None:
                    self.dial.enabled = False


            self.switch = Switch(27, 28, {
                "on": _on,
                "off": _off
            })
        elif self.layout == "v7":
            self.led = RgbLED(18, 19, 20)
            
            self.buttons = {
                "on": PushButton([10, 9], 'on'),
                "off": PushButton([5, 4], 'off'),
                "1": PushButton([12], 1),
                "2": PushButton([11], 2),
                "3": PushButton([7], 3),
                "4": PushButton([8], 4),
                "5": PushButton([0], 5),
                "6": PushButton([3], 6),
                "7": PushButton([1], 7),
                "8": PushButton([2], 8),
            }
        else:
            raise Exception("Unexpected config layout: " + str(self.layout))

        # Setup event handlers for buttons
        for button in self.buttons.values():
            def on_press(key: str):
                self._button_press(key)
                self.on_press(key)

            button.on_press = on_press

            button.on_long_press = lambda key : self.on_long_press(key)

            def on_release(key: str):
                self._button_unpress(key)
                self.on_release()

            button.on_release = on_release

        # Setup event handlers for the dial, if it exists
        if self.dial is not None:
            def on_dial_press(routine):
                self.on_dial_press(routine)

            self.dial.on_press = on_dial_press

            def on_dial_long_press(routine):
                self.on_dial_long_press(routine)

            self.dial.on_long_press = on_dial_long_press

    # A basic hook on button presses, to check if the user
    # is trying to trigger an update or not
    def _button_press(self, key):
        print("Pressed " + str(key))
        
        self._pressed[str(key)] = True
        
        self._should_update = self._could_update()
        if self._should_update:
            self._should_pair = False
            self.accepting_inputs = False
            self.preparing_update = True
            
            print("Update press detected")

            def upc(_):
                if self._could_update():
                    print("Checking for updates...")
                    self.on_update()
            
            if self._update_press_timer is not None:
                self._update_press_timer.deinit()

            self._update_press_timer = Timer(
                -1,
                mode=Timer.ONE_SHOT,
                period=Board.update_longpress_ms,
                callback=upc,
            )

        else:
            self._should_pair = self._could_pair()

            if self._should_pair:
                print("Pairing press detected")

                self.preparing_pairing = True
                self.accepting_inputs = False

                def ble_trigger(_):
                    if self._should_pair:
                        self.needs_pairing = True
            
                if self._ble_press_timer is not None:
                    self._ble_press_timer.deinit()
                
                self._ble_press_timer = Timer(
                    -1,
                    mode=Timer.ONE_SHOT,
                    period=Board.ble_longpress_ms,
                    callback=ble_trigger,
                )

    # Update state variables when buttons are released
    def _button_unpress(self, key):
        if str(key) in self._pressed:
            del self._pressed[str(key)]
        
        # If no longer preparing for an update, cancel the
        # timer and allow inputs again
        self._should_update = self._could_update()
        if self.preparing_update and not self._should_update:
            self.accepting_inputs = True
            self.preparing_update = False
            if self._update_press_timer is not None:
                self._update_press_timer.deinit()
        
        # If no longer preparing for BLE pairing, cancel the
        # timer and allow inputs again
        self._should_pair = self._could_pair()
        if self.preparing_pairing and not self.needs_pairing and not self._should_pair:
            self.preparing_pairing = False
            self.accepting_inputs = True
            if self._ble_press_timer is not None:
                self._ble_press_timer.deinit()
    
    # Holding two buttons indicates bluetooth pairing mode
    def _could_pair(self):
        return len(self._pressed) == 2
        
    # Holding four buttons checks for software updates
    def _could_update(self):
        return len(self._pressed) == 4
                
def setup(config):
    global shared

    if shared is not None:
        return

    shared = Board(config)


shared: Board | None = None
