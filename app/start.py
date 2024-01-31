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
        import app.board as board, app.wifi as wifi

        wifi.connect()
        otaUpdater = OTAUpdater('https://github.com/lucaspopp0/pico-switch', main_dir='app')
        board.led.do_color(10, 10, 10)
        
        print('Download new version (if pending)')
        if otaUpdater.install_update_if_available_after_boot(config.value["wifi"]["ssid"], config.value["wifi"]["pass"]):
            machine.reset()

        print('Check for new update to download')
        otaUpdater.check_for_update_to_install_during_next_reboot()
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

    config.read()
    board.setup()
    board.led.off()
    
    CHECK_RESTART_INTERVAL = 40
    CHECK_RESTART_TICKER = 0

    while True:
        CHECK_RESTART_TICKER += 1
        
        if CHECK_RESTART_TICKER >= CHECK_RESTART_INTERVAL:
            CHECK_RESTART_TICKER = 0
            refresh.restart_if_needed()
            
        board.request_queue.poll()


connectToWifiAndUpdate()
startApp()


