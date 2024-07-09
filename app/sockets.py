import socket
from . import config
from . import constants

homeAddr = socket.getaddrinfo(config.value["home-assistant-ip"], 8123)[0][-1]

def new_socket():
    s = socket.socket()
    s.settimeout(constants.socket_connect_s)
    s.connect(homeAddr)
    return s
