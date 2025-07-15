import asyncio
import errno

from .board import board, deprecated
from .config import config
from .requestqueue import request
from .wifi import wifi
from .otaupdate import update_manager

PROGRESS_COLOR = (0, 0, 50)
LONG_COLOR = (0, 50, 50)

def urlencode(txt):
    return txt.replace(' ', '%20')

def setup_handlers(shared_board: board.Board):
    if shared_board.led is not None:
        shared_board.on_release = on_release_rgbled
        shared_board.on_press = on_press_rgbled
        shared_board.on_long_press = on_longpress_rgbled
        shared_board.on_update = on_update

    if shared_board.dial is not None:
        shared_board.on_dial_press = on_dial_rgbled
        shared_board.on_dial_long_press = on_dial_long_rgbled

def _new_request(
    key: str,
    on_success=lambda : None,
    on_failure=lambda : None
):
    path = 'remote-press?remote=' + urlencode(config.value["name"]) + '&button=' + str(key)
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
            
            if wifi.failed_attempts == wifi.max_attempts:
                wifi.failed_attempts = 0
                wifi.can_check = True

def on_dial_long_rgbled(routine: deprecated.Routine):
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        print("Ignoring press, not accepting inputs right now")
        return
    
    req = _new_request(routine.name + "-long", on_success_rgbled, on_failure_rgbled)
    board.shared.led.do_color(0, 50, 50)
    _send_request(req)

def on_dial_rgbled(routine: deprecated.Routine):
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        print("Ignoring press, not accepting inputs right now")
        return
    
    req = _new_request(routine.name, on_success_rgbled, on_failure_rgbled)
    _send_request(req)

def on_press_rgbled(key: str):
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        print("Ignoring press, not accepting inputs right now")
        return
    
    req = _new_request(key, on_success_rgbled, on_failure_rgbled)
    board.shared.led.do_color(0, 0, 50)

    _send_request(req)

def on_release_rgbled():
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        return
    
    board.shared.led.off()

def on_longpress_rgbled(key: str):
    if board.shared is None or board.shared.led is None:
        return
    
    if not board.shared.accepting_inputs:
        print("Ignoring press, not accepting inputs right now")
        return
    
    longKey = key + "-long"
    req = _new_request(longKey, on_success_rgbled, on_failure_rgbled)
    board.shared.led.do_color(0, 50, 50)

    print("Sending " + req.path)

    _send_request(req)

def on_success_rgbled():
    if board.shared is None or board.shared.led is None:
        return
    
    board.shared.led.off()

def on_failure_rgbled():
    if board.shared is None or board.shared.led is None:
        return
    
    asyncio.run(board.shared.led.flash(100, 0, 0, times=2))

def on_update():
    update_manager.try_update()
