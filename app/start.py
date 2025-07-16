import asyncio

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

    # Setup the local HTTP server
    shared.api.start()

    # Try connecting to WiFi
    shared.wifi.connect()
    if not shared.wifi._connected:
        return

    # Start an infinite loop
    while True:
        # Should check for wifi, check for wifi
        if not shared.wifi._connected:
            shared.wifi.connect()

        # Check for request data
        shared.requestqueue.poll()

        # Check for updates on an interval
        if update_manager.should_check_update():
            update_manager.try_update()

try:
    start()
except KeyboardInterrupt as interrupt:
    print("Received interrupt. Shutting down")
