import select
import socket
import time
from . import sockets
from . import constants

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
            print("closing unknown socket")
            out[0][0].close()
            return

        req.recv()

        req.close()

        req.handle_response()

        self.requestsByPath[req.path].remove(req)

class Request:

    def __init__(self, path):
        self.path = path
        self.socket = None
        self.response = None

        self.expiry = None

        self.on_success = None
        self.on_failure = None

    def send(self, queue):
        if self.socket is not None:
            print("Too soon")

        self.socket = sockets.new_socket()
        queue.add(self)
        raw = b'POST /api/webhook/' + self.path + b' HTTP/1.1\r\n\r\n'
        print('Sending: ' + self.path)
        self.expiry = time.time() + constants.request_timeout_s
        self.socket.send(raw)

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

    def failed(self):
        err = parse_response(str(self.response))
        print('Request failed: ' + err)
        if self.on_failure is not None:
            self.on_failure(err)

    def close(self):
        self.socket.close()
        self.socket = None

def parse_response(response):
    ind = response.find("\r")
    if ind < 0:
        return response
    return response[0:ind]
