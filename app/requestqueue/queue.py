import select
import socket
from .request import Request


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

    def request_by_socket(self, sock: socket.Socket) -> Request | None:
        for req in self._requests:
            if req.socket == sock:
                return req

        return None

    # Adds a request to the queue, and send it
    def add(self, req: Request):
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
                self.poller.unregister(sock)

                req = self.request_by_socket(sock)
                if req is None:
                    print(
                        "socket in queue has data, but could not tie it to a request"
                    )
                    sock.close()
                    return

                self._handle_response(req)

    # Handle data from polling
    def _handle_response(self, req: Request):
        req.recv()
        req.close()
        req.handle_response()
        self._requests.remove(req)
