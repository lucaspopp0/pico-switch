import select
import time
import socket
import ujson
from . import config

request_timeout_s = 5
socket_connect_s = 2

def get_addr():
    port = 8123

    if config.use_ha_addon():
        port = 8124
    
    ip = config.value["home-assistant-ip"]
    return socket.getaddrinfo(ip, port)[0][-1]

def new_socket():
    s = socket.socket()
    s.settimeout(socket_connect_s)

    addr = get_addr()
    s.connect(addr)
    return s

def urlencode(txt):
    return txt.replace(' ', '%20')

class RequestQueue:

    def __init__(self):
        self.poller = select.poll()
        self.requestsByPath = {}

    def requestBySocket(self, sock):
        for path in self.requestsByPath:
            for req in self.requestsByPath[path]:
                if req.socket == sock:
                    return req

        return None

    # Adds a request to the queue
    # req - a Request
    def add(self, req):
        if not req.path in self.requestsByPath:
            self.requestsByPath[req.path] = []

        self.requestsByPath[req.path].append(req)

        self.poller.register(req.socket, select.POLLIN)

    def prune_queue(self):
        to_prune = []

        for path in self.requestsByPath:
            for req in self.requestsByPath[path]:
                if req.is_expired():
                    to_prune.append(req)

                    if len(self.requestsByPath[path]) == 1:
                        req.failed()

        for req in to_prune:
            self.requestsByPath[req.path].remove(req)

    def poll(self):
        out = self.poller.poll(500)

        if len(out) == 0:
            self.prune_queue()
            return

        self.poller.unregister(out[0][0])
        req = self.requestBySocket(out[0][0])

        if req is None:
            print("socket in queue has data, but could not tie it to a request")
            out[0][0].close()
            return

        req.recv()

        req.close()

        req.handle_response()

        self.requestsByPath[req.path].remove(req)

class Request:

    def __init__(self, path="", body=None):
        self.path = path
        self.body = body
        self.expiry = None

        self.socket = None
        self.response = None


        self.on_success = None
        self.on_failure = None

    def send(self, queue):
        if self.socket is not None:
            return

        self.socket = new_socket()
        queue.add(self)

        # Build HTTP request body
        http_lines = []

        if config.use_ha_addon():
            http_lines = [
                "PUT /api/press",
                "Content-Type: application/json"
                "",
                ujson.dumps(self.body),
                
            ]
        else:
            http_lines = [
                "POST /api/webhook/" + self.path + " HTTP/1.1",
                "",
            ]

        raw = "\r\n\r\n".join(http_lines)
        print('Sending: ' + raw)
        self.expiry = time.time() + request_timeout_s
        self.socket.send(raw.encode("utf-8"))

    def is_expired(self):
        if self.expiry is not None:
            return time.time() > self.expiry

        return False

    def recv(self):
        self.response = self.socket.recv(1000)

    def handle_response(self):
        if self.response.startswith(b'HTTP/1.1 200'):
            self.succeeded()
        else:
            self.failed()

    def succeeded(self):
        resp = parse_response(str(self.response))
        print('Request succeeded: ' + resp)
        if self.on_success is not None:
            self.on_success(resp)
        self.close()

    def failed(self):
        err = parse_response(str(self.response))
        print('Request failed: ' + err)
        if self.on_failure is not None:
            self.on_failure(err)
        self.close()

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

def parse_response(response):
    ind = response.find("\r")
    if ind < 0:
        return response
    return response[0:ind]
