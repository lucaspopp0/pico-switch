import select
import socket
from .request import Request

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
    def add(self, req: Request):
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
