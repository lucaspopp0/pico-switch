import time

from . import config
config.read()
config.read_version()

from . import board, wifi
board.setup()
    
def _board_set_wifi_connected(c):
    wifi.connected = c
    
    if wifi.failed_attempts == wifi.max_attempts:
        wifi.failed_attempts = 0
        wifi.can_check = True
    
board.set_wifi_connected = _board_set_wifi_connected

def startApp():
    print('Starting app')

    wifi.connect()
    board.led.off()
    
    if not wifi.is_connected():
        raise RuntimeError('wifi connection failed')
    
    board.accepting_inputs = True

    from . import update_manager
    from . import routes
    from .server import server
    from . import ble
    
    def ble_pairing():
        board.shared.led.do_color(50, 0, 50)
        ble.start_ble_on_demand()
        board.shared.led.off()
        time.sleep(0.2)
        board.shared.led.do_color(50, 0, 50)
        time.sleep(0.2)
        board.shared.led.off()

    svr = server.Server()
    routes.setup_routes(svr)
    svr.start()

    while True:
        if not wifi.is_connected() and wifi.can_check:
            wifi.connect()

        board.request_queue.poll()
        svr.poll()

        if update_manager.should_check_update():
            update_manager.try_update()
            
        if board.shared.needs_pairing:
            print("Pairing...")
            board.shared.needs_pairing = False
            ble_pairing()

startApp()
