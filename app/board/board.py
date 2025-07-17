import asyncio
from machine import Timer

from .basics import PushButton, RgbLED
from .deprecated import Routine, Wheel, Switch


class Board:

    update_longpress_ms = 5000
    pairing_longpress_ms = 5000

    def __init__(
        self,
        flipped: bool,
    ):
        # Basic metadata
        self.flipped = flipped

        self.accepting_inputs = False
        self.preparing_update = False
        self.preparing_pairing = False

        # A map of currently pressed keys
        self._pressed: dict[str, bool] = {}

        # State variables for special actions, automatically
        # updated based on the number of buttons pressed
        self._should_update = False
        self._should_pair = False

        # Timers for triggering special presses
        self._update_press_timer: Timer | None = None
        self._pair_press_timer: Timer | None = None

        self._wifi_connecting = False

        def on_press(key: str):
            pass
        self.on_press = on_press

        def on_release(key: str):
            pass
        self.on_release = on_release

        def on_update():
            pass
        self.on_update = on_update

        def on_pair():
            pass
        self.on_pair = on_pair

        def on_pair_cancel():
            pass
        self.on_pair_cancel = on_pair_cancel

    def enable(self):
        self.accepting_inputs = True

    def disable(self):
        self.accepting_inputs = False
    
    # Holding two buttons indicates bluetooth pairing mode
    def _could_pair(self):
        return len(self._pressed) == 2
        
    # Holding four buttons checks for software updates
    def _could_update(self):
        return len(self._pressed) == 4
        
    # Update state variables when buttons are pressed
    def _button_press(self, key):
        self._pressed[str(key)] = True
        
        # If four buttons are now pressed, start the
        # update press timer
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
            # If two buttons are now pressed, start the
            # pairing press timer
            self._should_pair = self._could_pair()
            if self._should_pair:
                print("Pairing press detected")

                self.preparing_pairing = True
                self.accepting_inputs = False

                def cbk(_):
                    if self._should_pair:
                        self.on_pair()
            
                if self._pair_press_timer is not None:
                    self._pair_press_timer.deinit()
                
                self._pair_press_timer = Timer(
                    -1,
                    mode=Timer.ONE_SHOT,
                    period=Board.pairing_longpress_ms,
                    callback=cbk,
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
        if self.preparing_pairing and not self._should_pair:
            self.preparing_pairing = False
            self.accepting_inputs = True
            if self._pair_press_timer is not None:
                self._pair_press_timer.deinit()

    def on_wifi_connecting(self):
        self._wifi_connecting = True

    def on_wifi_connected(self):
        self._wifi_connecting = False

    def on_wifi_failed(self, failure: str):
        self._wifi_connecting = False

class BasicButtonBoard(Board):

    def __init__(
        self,
        led: RgbLED,
        buttons: dict[str, PushButton],
        flipped = False,
    ):
        Board.__init__(self, flipped)

        self.led = led
        self.buttons = buttons

        # Setup event handlers for buttons
        for button in self.buttons.values():
            button.on_press = lambda key : self._on_button_press(key)
            button.on_long_press = lambda key : self._on_button_long_press(key)
            button.on_release = lambda key : self._on_button_release(key)

    def _on_button_press(self, key: str):
        self._button_press(key)

        if not self.accepting_inputs:
            return
        
        self.led.do_color(0, 0, 50)
        self.on_press(key)

    def _on_button_long_press(self, key: str):
        if not self.accepting_inputs:
            return
        
        self.led.do_color(0, 50, 50)
        self.on_press(key + '-long')

    def _on_button_release(self, key: str):
        self._button_unpress(key)
        self.on_release(key)

    def on_wifi_connecting(self):
        super().on_wifi_connecting()
        
        async def loop():
            on = False
            while self._wifi_connecting:
                if on:
                    self.led.off()
                else:
                    self.led.do_color(50, 0, 50)
                    
                on = not on
                await asyncio.sleep(0.2)

        asyncio.create_task(loop())
        self.enable()

    def on_wifi_connected(self):
        super().on_wifi_connected()

        # Flash blue
        asyncio.create_task(self.led.flash(0, 0, 50, times=2))

    def on_wifi_failed(self, failure: str):
        super().on_wifi_failed(failure)

        # Flash the LED
        asyncio.create_task(self.led.flash(50, 0, 0, times=3))

class DialBoard(BasicButtonBoard):

    def __init__(
        self,
        led: RgbLED,
        buttons: dict[str, PushButton],
        dial: Wheel,
        wheel_routines: list[dict],
        switch: Switch | None = None,
        flipped = False,
    ):
        BasicButtonBoard.__init__(
            self,
            led=led,
            buttons=buttons,
            flipped=flipped,
        )

        self.switch = switch
        
        # Set up the dial
        dialScenes = []
        if wheel_routines is not None:
            for routine in wheel_routines:
                scene = Routine(routine["name"], routine["rgb"], 0)
                dialScenes.append(scene)
        
        self.dial = dial
        self.dial.size = len(dialScenes)
        self.dial.options = dialScenes

        def on_dial_press(routine: Routine):
            pass

        self.on_dial_press = on_dial_press
        self.on_dial_longpress = on_dial_press

        def _on_dial_press(routine: Routine):
            if self.on_dial_press is not None:
                self.on_dial_press(routine)

        def _on_dial_longpress(routine: Routine):
            if self.on_dial_longpress is not None:
                self.on_dial_longpress(routine)

        self.dial.on_press = _on_dial_press
        self.dial.on_long_press = _on_dial_longpress

    def _dial_press(self, routine: Routine):
        self.on_dial_press(routine)

    def enable(self):
        super().enable()
        self.dial.enabled = True
    
    def disable(self):
        super().disable()
        self.dial.enabled = False
