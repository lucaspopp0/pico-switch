import time
from . import wifi
from . import board
from . import config

board.led.off()
config.read()
wifi.connect()

while True:
    board.request_queue.poll()
