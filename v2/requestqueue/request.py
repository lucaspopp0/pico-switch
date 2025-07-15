import select
import time
import socket

# Handlers for a single HTTP request
class Request:

    request_timeout_s = 5

    @staticmethod
    def parse_response(response: str) -> str:
        ind = response.find("\r")
        if ind < 0:
            return response
        return response[0:ind]

    def __init__(self, path):
        self.path = path
        self.socket: socket.Socket | None = None
        self.bytes_received: bytes = bytes([])

        self.expiry = None

        self.on_success = lambda : None
        self.on_failure = lambda : None

    def send(self, sock: socket.Socket):
        self.socket = sock
        self.expiry = time.time() + Request.request_timeout_s
        self.bytes_received = bytes([])

        print('Sending: ' + self.path)
        raw = b'POST /api/webhook/' + self.path + b' HTTP/1.1\r\n\r\n'
        self.socket.send(raw)

    def is_expired(self):
        if self.expiry is not None:
            return time.time() > self.expiry

        return False

    def recv(self):
        if self.socket is not None:
            self.bytes_received = self.socket.recv(1000)

    def handle_response(self):
        if self.bytes_received.startswith(b'HTTP/1.1 200'):
            self.succeeded()
        else:
            self.failed()

    # Called on HTTP 200
    # Calls the on_success hook, if one is set
    def succeeded(self):
        resp = Request.parse_response(str(self.bytes_received))
        print('Request succeeded: ' + resp)
        self.on_success()
        self.close()

    # Called on HTTP 4xx/5xx
    # Calls the on_failure hook, if one is set
    def failed(self):
        err = Request.parse_response(str(self.bytes_received))
        print('Request failed: ' + err)
        self.on_failure()
        self.close()

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
