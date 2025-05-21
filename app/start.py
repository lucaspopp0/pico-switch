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

def tryUpdate():
    import machine, gc

    try:
        from .ota_updater.ota_updater import OTAUpdater
        from . import board

        headers = {}
        if "github-token" in config.value:
            headers["Authorization"] = "Bearer " + str(config.value["github-token"])
            headers["X-GitHub-Api-Version"] = "2022-11-28"

        otaUpdater = OTAUpdater(board.led, 'https://github.com/lucaspopp0/pico-switch', main_dir='app')

        if otaUpdater.install_update_if_available():
            machine.reset()
        else:   
            board.led.off()

        del(otaUpdater)
        gc.collect()
    except Exception as e:
        print(e)

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

    svr = server.Server()
    routes.setup_routes(svr)
    svr.start()
    
    # Start BLE server
    ble.start_ble_server()

    while True:
        if not wifi.is_connected() and wifi.can_check:
            wifi.connect()

        board.request_queue.poll()
        svr.poll()

        if update_manager.should_check_update():
            tryUpdate()

startApp()
