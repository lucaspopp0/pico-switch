import time

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

    # Setup the HTTP server
    svr = server.Server()
    routes.setup_routes(svr)
    svr.start()

    # Start an infinite loop
    while True:
        # Should check for wifi, check for wifi
        if not wifi.is_connected() and wifi.can_check:
            wifi.connect()

        # Check for request data
        request.shared_queue.poll()

        # Poll for server requests
        svr.poll()

        # Check for updates on an interval
        if update_manager.should_check_update():
            update_manager.try_update()

        # Handle pairing requests
        if board.shared.needs_pairing:
            print("Pairing...")
            ble_pairing()
            board.shared.needs_pairing = False


try:
    startApp()
except KeyboardInterrupt as interrupt:
    print("Received interrupt. Shutting down")

    try:
        board.shared.led.off()
    finally:
        pass
