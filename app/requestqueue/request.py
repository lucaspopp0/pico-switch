import select
import time
import socket

# Polls multiple sockets in parallel, allowing sending
# requests and then waiting for responses without blocking
# the event loop
class RequestQueue:

    socket_connect_s = 2

    @staticmethod
    def new_socket(host: str) -> socket.Socket:
        sock = socket.socket()
        sock.settimeout(RequestQueue.socket_connect_s)
        sock.connect(host)
        return sock

    def __init__(self, capacity: int, host: str):
        self.host = host

        # Create a new poller, which can be used to poll
        # multiple sockets in parallel
        self.poller = select.poll()
        
        # Set up a list of requests for the queue
        self._requests: list[Request] = []
        self.capacity = capacity


    def request_by_socket(self, sock: socket.Socket):
        for req in self._requests:
            if req.socket == sock:
                return req

        return None

    # Adds a request to the queue, and send it
    def add(self, req):
        if len(self._requests) >= self.capacity:
            print("Request queue at capacity")
            return

        self._requests.append(req)
        req.socket = RequestQueue.new_socket(self.host)

        self.poller.register(req.socket, select.POLLIN)
        req.send(req.socket)

    # Trigger timeouts
    def prune_queue(self):
        to_prune = []

        for req in self._requests:
            if req.is_expired():
                to_prune.append(req)

        for req in to_prune:
            self._requests.remove(req)
            req.failed()

    # Poll any active sockets for data
    def poll(self):
        events = self.poller.poll(500)

        if len(events) == 0:
            # Nothing to process, use this time to clean up!
            self.prune_queue()
            return
        
        # Handle results from polling
        for sock, event in events:
            if event & select.POLLIN:
                self.on_sock_data(sock)

    # Handle data from polling
    def on_sock_data(self, sock: socket.Socket):
        self.poller.unregister(sock)

        req = self.request_by_socket(sock)
        if req is None:
            print("socket in queue has data, but could not tie it to a request")
            sock.close()
            return

        req.recv()
        req.close()
        req.handle_response()
        self._requests.remove(req)

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

    def send(self, socket: socket.Socket):
        self.socket = socket
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
