import asyncio
import errno

from .board import board
from . import config
from . import request
from . import wifi

PROGRESS_COLOR = (0, 0, 50)
LONG_COLOR = (0, 50, 50)

def _new_request(
    key: str,
    on_success=lambda : None,
    on_failure=lambda : None
):
    path = 'remote-press?remote=' + request.urlencode(config.value["name"]) + '&button=' + str(key)
    req = request.Request(path)

    req.on_success = on_success
    req.on_failure = on_failure

    return req

def _send_request(req: request.Request):
    if request.shared_queue is None:
        return
    
    try:
        req.send(request.shared_queue)
    except OSError as oserr:
        print("Failed to send: " + str(oserr))
            
        req.failed()
    
        # If the host was unreachable, try to reconnect
        # to wifi
        if oserr.args[0] == errno.EHOSTUNREACH:
            wifi.connected = False

def on_press_rgbled(key: str):
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        print("Ignoring press, not accepting inputs right now")
        return
    
    req = _new_request(key, on_success_rgbled, on_failure_rgbled)
    board.shared.led.do_color(0, 0, 50)

    _send_request(req)

def on_longpress_rgbled(key: str):
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        print("Ignoring press, not accepting inputs right now")
        return
    
    longKey = key + "-long"
    req = _new_request(longKey, on_success_rgbled, on_failure_rgbled)
    board.shared.led.do_color(0, 50, 50)

    _send_request(req)

def on_success_rgbled(key: str):
    if board.shared is None or board.shared.led is None:
        return
    
    board.shared.led.off()

def on_failure_rgbled():
    if board.shared is None or board.shared.led is None:
        return
    
    asyncio.run(board.shared.led.flash(100, 0, 0, times=2))
