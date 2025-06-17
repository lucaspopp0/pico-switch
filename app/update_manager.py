import time
import os

_dir = "app"
_last_restart_file_name = ".last-restart"

_last_restart_day = 0
_check_ticker_interval = 80
_check_ticker = _check_ticker_interval

def should_check_update():
    (_, _, day, hour, _, _, _, _) = time.localtime()
    last_update_day = last_update()

    if last_update_day != day and hour == 10:
        record_update(day)
        return True
    return False

def last_update():
    global _check_ticker, _check_ticker_interval, _last_restart_day

    # Only check every 80 times, to reduce load on the underlying file
    _check_ticker += 1
    if _check_ticker < _check_ticker_interval:
        return _last_restart_day
    
    if _last_restart_file_name in os.listdir(_dir):
        with open(_dir + '/' + _last_restart_file_name) as f:
            _check_ticker = 0
            _last_restart_day = int(f.read())
            return _last_restart_day
        
    return -1

def record_update(day):
    with open(_dir + '/' + _last_restart_file_name, 'w') as last_restart_file:
        last_restart_file.write(str(day))
        last_restart_file.close()

def try_update():
    import machine, gc

    try:
        from .ota_updater.ota_updater import OTAUpdater
        from . import board, config

        headers = {}
        if "github-token" in config.value:
            headers["Authorization"] = "Bearer " + str(config.value["github-token"])
            headers["X-GitHub-Api-Version"] = "2022-11-28"

        otaUpdater = OTAUpdater(board.shared.led, 'https://github.com/lucaspopp0/pico-switch', main_dir='app')

        if otaUpdater.install_update_if_available():
            machine.reset()
        else:   
            board.shared.led.off()

        del(otaUpdater)
        gc.collect()
    except Exception as e:
        print(e)
