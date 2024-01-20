from . import wifi
import uasyncio
import urequests
import ujson
import select

def urlencode(txt):
    return txt.replace(' ', '%20')

async def sendcmd(cmd):
    print('cmd: ' + cmd)
    body = ujson.dumps({ 'cmd': cmd })
    print(body)
    response = urequests.post('http://192.168.4.31:3002/cmd', headers={'x-api-key':'abcd1234','content-type':'application/json'}, data=body)
    response.close()

async def sendpress(key):
    await sendbasic('remote-press?remote=' + urlencode('New Bedroom') + '&button=' + str(key))

async def sendbasic(path):
    p = select.poll()
    s = wifi.new_socket()
    p.register(s, select.POLLIN)
    s.send(b'POST /api/webhook/' + path + b' HTTP/1.1\r\n\r\n')
    res = p.poll(500)
    print(res[0][0])
    #response = urequests.post('http://192.168.86.44:8123/api/webhook/' + path)
    #response.close()
    s.close()

async def send(routine, scene, room):
    await sendbasic('generic-routine?routine=' + routine + '&cmd=' + scene + '&room=' + room)
