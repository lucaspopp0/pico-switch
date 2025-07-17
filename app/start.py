import asyncio

<<<<<<< HEAD
def start():
    from . import shared
    from .otaupdate import update_manager

    # Set everything up
    shared.setup_config()
    shared.setup_request_queue()
    shared.setup_board()
    shared.setup_wifi()
    shared.setup_bluetooth()
    shared.setup_automatic_updates()
    shared.setup_api()

    # Try connecting to WiFi
    shared.wifi.connect()
    if not shared.wifi._connected:
        return
=======
from . import config

config.read()
config.read_version()

from .board import board

board.setup(config.value)


def startApp():
    if board.shared is None:
        return

    print('Starting app')
    from . import handlers
    handlers.setup_handlers(board.shared)

    # Connect to wifi
    from . import wifi
    wifi.connect()
    board.shared.led.off()

    # If connection fails, bail out
    if not wifi.is_connected():
        raise RuntimeError('wifi connection failed')

    # Enable the board
    board.shared.accepting_inputs = True

    # Setup the request queue
    from . import request
    request.setup_shared_queue()

    # Setup the BLE pairing callback
    from . import update_manager
    from . import routes
    from .server import server
    from . import ble

    def ble_pairing():
        board.accepting_inputs = False
        board.shared.led.do_color(50, 0, 50)
        ble.start_ble_on_demand()
        board.shared.led.off()
        time.sleep(0.2)
        board.shared.led.do_color(50, 0, 50)
        time.sleep(0.2)
        board.shared.led.off()
        board.accepting_inputs = True
>>>>>>> v2

    # Setup the HTTP server
    shared.api.start()

    # Start an infinite loop
    while True:
        # Should check for wifi, check for wifi
        if not shared.wifi._connected:
            shared.wifi.connect()

        # Check for request data
        shared.requestqueue.poll()

        # Poll for api requests
        shared.api.poll()

        # Check for updates on an interval
        if update_manager.should_check_update():
            update_manager.try_update()
<<<<<<< HEAD
=======

        # Handle pairing requests
        if board.shared.needs_pairing:
            print("Pairing...")
            ble_pairing()
            board.shared.needs_pairing = False
>>>>>>> v2


try:
    start()
except KeyboardInterrupt as interrupt:
    print("Received interrupt. Shutting down")
<<<<<<< HEAD
=======

    try:
        board.shared.led.off()
    finally:
        pass
>>>>>>> v2
