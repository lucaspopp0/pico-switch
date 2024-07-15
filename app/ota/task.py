import socket, select
import ujson
import gc

class Task:

    def __init__(self):
        self.started = False
        self.done = False

    def reset(self):
        self.started = False
        self.done = False

    def in_progress(self):
        return self.started and not self.done

class HttpTask(Task):

    def __init__(self, url, headers={}, saveToFile=None):
        super().__init__(self)

        self.url = url
        self.headers = headers
        self._saveToFile = saveToFile
        self._saveFile = None

        self.headers_task = Task()
        self.body_task = Task()

        self.poller = select.poll()
        self.socket = None
        self.data = None


        self.response_status = None
        self.response_reason = ''

    def start(self):
        if self.started:
            return

        self.started = True

        def _write_headers(sock, _headers):
            for k in _headers:
                sock.write(b'{}: {}\r\n'.format(k, _headers[k]))

        try:
            proto, dummy, host, path = url.split('/', 3)
        except ValueError:
            proto, dummy, host = url.split('/', 2)
            path = ''
        if proto == 'http:':
            port = 80
        elif proto == 'https:':
            import ussl
            port = 443
        else:
            raise ValueError('Unsupported protocol: ' + proto)

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)

        ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        if len(ai) < 1:
            raise ValueError('You are not connected to the internet...')
        ai = ai[0]

        s = socket.socket(ai[0], ai[1], ai[2])
        self.socket = s
        try:
            s.connect(ai[-1])
            if proto == 'https:':
                gc.collect()
                s = ussl.wrap_socket(s, server_hostname=host)
            s.write(b'GET /%s HTTP/1.0\r\n' % (path))
            if not 'Host' in self.headers:
                s.write(b'Host: %s\r\n' % host)
            # Iterate over keys to avoid tuple alloc
            _write_headers(s, self._headers)

            # add user agent
            s.write(b'User-Agent: MicroPython Client\r\n')
            s.write(b'\r\n')

            self.poller.register(s, select.POLLIN)
        except OSError:
            s.close()
            self.socket = None
            raise

    def recv(self):
        result = self.poller.poll(500)
        if len(result) == 0:
            return

        redirect = None #redirection url, None means no redirection

        try:
            if self.headers_task.in_progress():
                l = self.socket.readline()
                l = l.split(None, 2)
                self.response_status = int(l[1])
                self.response_reason = ''
                if len(l) > 2:
                    self.response_reason = l[2].rstrip()
                while True:
                    l = self.socket.readline()
                    if not l or l == b'\r\n':
                        break
                    #print('l: ', l)
                    if l.startswith(b'Transfer-Encoding:'):
                        if b'chunked' in l:
                            raise ValueError('Unsupported ' + l)
                    elif l.startswith(b'Location:') and not 200 <= self.response_status <= 299:
                        if self.response_status in [301, 302, 303, 307, 308]:
                            redirect = l[10:-2].decode()
                        else:
                            raise NotImplementedError("Redirect {} not yet supported".format(status))

                self.headers_task.done = True
                self.body_task.started = True
            elif not self.headers_task.started:
                self.headers_task.started = True
                if self._saveToFile is not None:
                    with open(self._saveToFile, 'w') as outfile:
                        self._saveFile = outfile
            elif self.body_task.in_progress():
                if self._saveToFile is not None:
                    CHUNK_SIZE = 512 # bytes
                    data = self._socket.recv(CHUNK_SIZE)
                    if data is None:
                        self.body_task.done = True
                        self.socket.close()
                    else:
                        self._saveFile.write(data)
                else:
                    self.data = ujson.load(self.socket)
                    self.socket.close()
                    self.body_task.done = True
            elif self.body_task.done:
                self.done = True
        except OSError:
            self.socket.close()
            raise

        if redirect:
            self.socket.close()
            self.url = redirect
            self.reset()
            self.start()
