from machine import Pin

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