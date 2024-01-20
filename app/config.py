import ujson

file_name = 'config.json'

value = None

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
            value = {}
        
def write():
    with open(file_name, 'w') as f:
        ujson.dump(value, f)
