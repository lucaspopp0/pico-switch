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

    def __init__(
        self,
        path: str,
        body: str = '',
    ):
        self.path = path
        self.body = body
        self.socket: socket.Socket | None = None
        self.bytes_received: bytes = bytes([])

        self.expiry = None

        self.on_success = lambda: None
        self.on_failure = lambda: None

    # Send a request into the provided socket!
    def send(self, socket: socket.Socket):
        self.socket = socket
        self.expiry = time.time() + Request.request_timeout_s
        self.bytes_received = bytes([])

        print('Sending: ' + self.path)
        raw = b'POST /api/webhook/' + self.path.encode('utf-8')
        raw += b' HTTP/1.1\r\n\r\n'
        raw += self.body.encode('utf-8')
        self.socket.send(raw)

    # Check for timeout
    def is_expired(self):
        if self.expiry is not None:
            return time.time() > self.expiry

        return False

    # Receive data from the socket
    def recv(self):
        if self.socket is not None:
            self.bytes_received = self.socket.recv(1000)

    # Handle the response
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

    # Close the socket
    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None
