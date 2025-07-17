import json
import machine
import binascii

file_name = 'config.json'
version_file = 'app/.version'

default_value = {}
default_version = 'v0.0.0'

value = None

version = None

uuid = binascii.hexlify(machine.unique_id()).upper()


def info():
    global uuid, version, value
    safe_value = value.copy()
    del safe_value["wifi"]
    return json.dumps({
        "_uuid": uuid,
        "_version": version,
        "config": safe_value,
    })


def read():
    global value
    try:
        with open(file_name, 'r') as f:
            value = json.load(f)
    except Exception as e:
        if value is not None:
            raise e
        else:
            print(e)
            value = default_value


def write():
    with open(file_name, 'w') as f:
        json.dump(value, f)


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
