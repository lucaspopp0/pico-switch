def start():
    # Load the config
    from .config.config import Config
    config = Config()
    config.load()

    # Configure the board
    from .board import board
    board.setup(config)

    # Configure the WiFi connection

    # Start the event loop

try:
    start()
except KeyboardInterrupt as interrupt:
    print("Received interrupt. Shutting down")
