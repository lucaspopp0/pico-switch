import network
import time
from .board import board
import asyncio
from . import config
from machine import Timer

httpOK = b'HTTP/1.1 200'

wlan = network.WLAN(network.STA_IF)

connected = False
current_ip = None

can_check = True

can_check_timer = None

max_attempts = 5
failed_attempts = 0


def is_connected():
    global connected
    return wlan.isconnected() and connected


def connect():
    global connected, can_check, can_check_timer, failed_attempts, max_attempts, current_ip

    if not can_check:
        return

    wlan.active(True)
    wlan.connect(config.value['wifi']['ssid'], config.value['wifi']['pass'])

    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print('waiting for wifi...')
        board.shared.do_color(15, 15, 0)
        time.sleep(0.3)
        board.shared.do_color(0, 0, 0)
        time.sleep(0.7)

    def check(tmr):
        global can_check, failed_attempts, max_attempts
        can_check = failed_attempts < max_attempts
        tmr.deinit()
        can_check_timer = None

    if wlan.status() != 3:
        failed_attempts += 1
        connected = False
        asyncio.run(board.shared.flash(30, 0, 0, times=5, seconds=0.3))
        print('wifi connection failed')
    else:
        failed_attempts = 0
        connected = True
        status = wlan.ifconfig()
        current_ip = status[0]
        print('wifi connected! ip = ' + current_ip)
        
        if board.shared.layout == 'v8':
            board.shared.neopixels.set_all((0, 0, 0))
            board.shared.neopixels.set_button('off', (3, 1, 0))
        else:
            asyncio.run(board.shared.flash(0, 0, 30, times=2))

    can_check = False
    can_check_timer = Timer().init(mode=Timer.ONE_SHOT,
                                   period=5000,
                                   callback=check)
