def connectToWifiAndUpdate():
    import time, machine, network, gc, app.config as config
    time.sleep(1)
    print('Memory free', gc.mem_free())

    config.read()

    from app.ota_updater.ota_updater import OTAUpdater

    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(config.value["wifi"]["ssid"], config.value["wifi"]["pass"])
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
    otaUpdater = OTAUpdater('https://github.com/lucaspopp0/pico-switch', main_dir='app')
    hasUpdated = otaUpdater.install_update_if_available()
    if hasUpdated:
        machine.reset()
    else:
        del(otaUpdater)
        gc.collect()

def startApp():
    from . import wifi
    from . import board
    from . import config

    board.led.off()
    config.read()
    wifi.connect()

    print("New version :)")

    while True:
        board.request_queue.poll()


connectToWifiAndUpdate()
startApp()