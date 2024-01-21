def connectToWifiAndUpdate():
    import time, machine, network, gc
    time.sleep(1)
    print('Memory free', gc.mem_free())

    try:
        from app.ota_updater.ota_updater import OTAUpdater
        import app.config as config
        config.read()

        import app.board as board, app.wifi as wifi
        board.setup()

        wifi.connect()
        otaUpdater = OTAUpdater('https://github.com/lucaspopp0/pico-switch', main_dir='app')

        if otaUpdater.check_for_update_to_install_during_next_reboot():
            board.led.do_color(50, 10, 0)

        hasUpdated = otaUpdater.install_update_if_available()
        if hasUpdated:
            machine.reset()
        else:
            del(otaUpdater)
            gc.collect()
    except Exception as e:
        print(e)

def startApp():
    from . import wifi
    from . import board
    from . import config

    config.read()
    board.setup()
    board.led.off()
    wifi.connect()

    while True:
        board.request_queue.poll()


connectToWifiAndUpdate()
startApp()