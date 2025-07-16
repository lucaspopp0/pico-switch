def start():
    from . import shared

    # Load the config
    from .config.config import Config
    shared.config = Config()
    shared.config.load()

    # Configure the request queue
    from .requestqueue.queue import RequestQueue
    shared.requestqueue = RequestQueue(
        5,
        shared.config.value['homeassistant-ip'],
    )

    # Configure the board
    shared.board = shared.setup_board()

    # Configure the WiFi connection
    ssid, psk, ok = shared.config.value.get_wifi()
    if not ok:
        return
    
    from .wifi.wifi import WiFiController
    shared.wifi = WiFiController(ssid, psk)

    # TODO: Setup handlers

    shared.wifi.connect()

    if not shared.wifi._connected:
        return

    # Event loop
    while True:
        # Check the request queue for responses
        shared.requestqueue.poll()

try:
    start()
except KeyboardInterrupt as interrupt:
    print("Received interrupt. Shutting down")
