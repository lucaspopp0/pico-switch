def connectToWifiAndUpdate():
    import time, machine, network, gc
    
    try:
        import app.config as config
        config.read()
        
        import app.board as board
        board.setup()
        board.led.do_color(10, 10, 10)
    except Exception as e:
        print(e)

    try:
        from app.ota_updater.ota_updater import OTAUpdater
        import app.board as board
        import app.wifi as wifi
        import app.config as config
        config.read()
        
        headers = {}
        if "github-token" in config.value:
            headers["Authorization"] = "Bearer " + str(config.value["github-token"])
            headers["X-GitHub-Api-Version"] = "2022-11-28"

        wifi.connect()
        otaUpdater = OTAUpdater('https://github.com/lucaspopp0/pico-switch', main_dir='app')
        board.led.do_color(10, 10, 10)
        
        if otaUpdater.install_update_if_available():
            machine.reset()
            
        del(otaUpdater)
        gc.collect()
    except Exception as e:
        print(e)

def startApp():
    print('Starting app')
    
    from . import wifi
    from . import board
    from . import config
    from . import refresh
    from . import routes
    from .server import server

    config.read_version()
    config.read()
    board.setup()
    board.led.off()
    
    svr = server.Server()
    routes.setup_routes(svr)
    svr.start()
    
    CHECK_RESTART_INTERVAL = 40
    CHECK_RESTART_TICKER = 0

    while True:
        CHECK_RESTART_TICKER += 1
        
        if CHECK_RESTART_TICKER >= CHECK_RESTART_INTERVAL:
            CHECK_RESTART_TICKER = 0
            refresh.restart_if_needed()
        
        board.request_queue.poll()
        svr.poll()


connectToWifiAndUpdate()
startApp()


