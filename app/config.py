import ujson
import machine
import ubinascii

file_name = 'config.json'
version_file = 'app/.version'

default_value = {}
default_version = 'v0.0.0'

value = None

version = None

uuid = ubinascii.hexlify(machine.unique_id()).upper()

def info():
    global uuid, version, value
    safe_value = value.copy()
    del safe_value["wifi"]
    return ujson.dumps({
        "_uuid": uuid,
        "_version": version,
        "config": safe_value,
    })

def read():
    global value
    try:
        with open(file_name, 'r') as f:
            value = ujson.load(f)
    except Exception as e:
        if value is not None:
            raise e
        else:
            print(e)
            value = default_value

def write():
    with open(file_name, 'w') as f:
        ujson.dump(value, f)

def read_version():
    global version
    try:
        with open(version_file, 'r') as f:
            version = f.read().replace('[\n\r\t ]', '')
    except Exception as e:
        if version is not None:
            raise e
        else:
            print(e)
            version = default_version

def use_ha_addon():
    if "enable_ha_addon" in value:
        if value["enable_ha_addon"]:
            return True
        
    return False
