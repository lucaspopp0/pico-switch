from .. import config


def get_info(server):
    server.send("HTTP/1.0 200 OK\r\n")
    server.send("Content-Type: application/json\r\n\r\n")
    server.send(config.info())


def get_device_xml(server):
    """Generate UPnP device description XML for SSDP discovery."""
    cfg = config.get()
    uuid = config.Config.device_uuid()
    version = config.version()

    # Extract device name and layout from config
    device_name = cfg.value.get('name', 'Pico Smart Switch')
    layout = cfg.value.get('layout', 'unknown')

    # Build XML response
    xml = f'''<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <deviceType>urn:schemas-lucaspopp0:device:SmartSwitch:1</deviceType>
    <friendlyName>{device_name}</friendlyName>
    <manufacturer>Lucas Popp</manufacturer>
    <modelName>Pico Smart Switch</modelName>
    <modelNumber>{layout}</modelNumber>
    <UDN>uuid:{uuid}</UDN>
  </device>
</root>'''

    server.send("HTTP/1.0 200 OK\r\n")
    server.send("Content-Type: text/xml\r\n\r\n")
    server.send(xml)


def setup_routes(server):
    server.add_route(path="/info", handler=lambda r: get_info(server))
    server.add_route(path="/device.xml",
                     handler=lambda r: get_device_xml(server))
