from . import config
config.read()
config.read_version()

from . import board, wifi
board.setup()

def tryUpdate():
    import machine, gc

    try:
        from .ota_updater.ota_updater import OTAUpdater
        from . import board

        headers = {}
        if "github-token" in config.value:
            headers["Authorization"] = "Bearer " + str(config.value["github-token"])
            headers["X-GitHub-Api-Version"] = "2022-11-28"

        otaUpdater = OTAUpdater('https://github.com/lucaspopp0/pico-switch', main_dir='app')
        board.led.do_color(5, 1, 0)

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

    from . import update_manager
    from . import routes
    from .server import server

    svr = server.Server()
    routes.setup_routes(svr)
    svr.start()

    while True:
        board.request_queue.poll()
        svr.poll()

        if True:
            tryUpdate()

startApp()
