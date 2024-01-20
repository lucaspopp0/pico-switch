import socket
from . import config

homeAddr = socket.getaddrinfo('192.168.86.44', 8123)[0][-1]

def new_socket():
    s = socket.socket()
    s.settimeout(10)
    s.connect(homeAddr)
    return s
