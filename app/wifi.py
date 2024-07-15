import network
import time
from . import board
import uasyncio
from . import config
from .lib import nptime

httpOK = b'HTTP/1.1 200'

wlan = network.WLAN(network.STA_IF)

def is_connected():
    return wlan.isconnected()

def connect():
    wlan.active(True)
    wlan.connect(config.value['wifi']['ssid'], config.value['wifi']['pass'])

    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if is_connected():
            break
        max_wait -= 1
        print('waiting for wifi...')
        board.led.do_color(100, 100, 0)
        time.sleep(0.3)
        board.led.off()
        time.sleep(0.7)

    if wlan.status() != 3:
        uasyncio.run(board.led.flash(100, 0, 0, times=5, seconds=0.3))
        raise RuntimeError('wifi connection failed')
    else:
        status = wlan.ifconfig()
        print('wifi connected! ip = ' + status[0] )
        nptime.settime()
        uasyncio.run(board.led.flash(0, 0, 50, times=2))


