import time
import machine
import os

_dir = "app"
_last_restart_file_name = ".last-restart"

def restart_if_needed():    
    (_, _, day, hour, minute, second, _, _) = time.localtime()
    last_restart_day = last_restart()
    
    if last_restart_day != day and hour == 3:
        record_restart(day)
        machine.reset()

def last_restart():
    if _last_restart_file_name in os.listdir(_dir):
        with open(_dir + '/' + _last_restart_file_name) as f:
            last_restart_day = f.read()
            return int(last_restart_day)
    return -1

def record_restart(day):
    with open(_dir + '/' + _last_restart_file_name, 'w') as last_restart_file:
        last_restart_file.write(str(day))
        last_restart_file.close()
