from . import config

def get_info(server):
    server.send("HTTP/1.0 200 OK\r\n")
    server.send("Content-Type: application/json\r\n\r\n")
    server.send(config.info())

def setup_routes(server):
    server.add_route(path="/info", handler=lambda r : get_info(server))
