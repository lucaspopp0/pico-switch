import select
import time
import socket

# Polls multiple sockets in parallel, allowing sending
# requests and then waiting for responses without blocking
# the event loop
class RequestQueue:

    socket_connect_s = 2

    def __init__(self, host: str):
        # A poller, which can be used to poll multiple sockets in parallel
        self.poller = select.poll()
        self.requestsByPath: dict[str, list[Request]] = {}
        self.host = host

    def new_socket(self) -> socket.Socket:
        sock = socket.socket()
        sock.settimeout(RequestQueue.socket_connect_s)
        sock.connect(self.host)
        return sock

    def requestBySocket(self, sock: socket.Socket):
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
