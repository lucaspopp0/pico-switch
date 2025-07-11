import select
import time
import socket
from . import config

request_timeout_s = 2
retries = 3
socket_connect_s = 2

homeAddr = None

def new_socket():
    global homeAddr
    if homeAddr is None:
        homeAddr = socket.getaddrinfo(config.value["home-assistant-ip"], 8123)[0][-1]

    s = socket.socket()
    s.settimeout(socket_connect_s)
    s.connect(homeAddr)
    return s

def urlencode(txt):
    return txt.replace(' ', '%20')

class RequestQueue:

    def __init__(self):
        self.poller = select.poll()
        self.requestsByPath: dict[string, Request] = {}

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
        
        def on_failure():
            global retries
            if req.retry < retries:
                print("Retrying...")
                req.retry += 1
                req.send(self)
            else:
                req.on_failure()

        req.recv()

        req.close()

        req.handle_response()

        self.requestsByPath[req.path].remove(req)

class Request:

    def __init__(self, path):
        self.path = path
        self.socket = None
        self.response = None
        self.retry = 0

        self.expiry = None

        self.on_success = lambda response : None
        self.on_failure = lambda response : None

    def send(self, queue):
        global retries
        
        if self.socket is not None:
            return
            
        for self.retry in range(retries):
            try:
                self.socket = new_socket()
                queue.add(self)
                raw = b'POST /api/webhook/' + self.path + b' HTTP/1.1\r\n\r\n'
                print('Sending: ' + self.path)
                self.expiry = time.time() + request_timeout_s
                self.socket.send(raw)
                return
            except OSError as err:
                if self.retry + 1 < retries:
                    print(err)
                else:
                    raise err

    def is_expired(self):
        if self.expiry is not None:
            return time.time() > self.expiry

        return False

    def recv(self):
        if self.socket is not None:
            self.response = self.socket.recv(1000)

    def handle_response(self):
        if (
            self.response is not None
            and self.response.startswith(b'HTTP/1.1 200')
        ):
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
