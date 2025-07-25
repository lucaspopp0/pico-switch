import asyncio
from ..lib import aioble
import bluetooth
from .. import shared

_ADV_INTERVAL_US = 250000

# Service UUID for our device (custom UUID for Pico-Switch)
DEVICE_SERVICE_UUID = bluetooth.UUID("DF82C9F9-D7B4-47F0-914F-788B3B2AB9A1")

# Characteristic UUIDs for our device
TYPE_CHAR_UUID = bluetooth.UUID("19B10001-E8F2-537E-4F6C-D104768A1214")
NAME_CHAR_UUID = bluetooth.UUID("19B10001-E8F2-537E-4F6C-D104768A1214")
LAYOUT_CHAR_UUID = bluetooth.UUID("19B10002-E8F2-537E-4F6C-D104768A1214")
VERSION_CHAR_UUID = bluetooth.UUID("19B10003-E8F2-537E-4F6C-D104768A1214")
IP_CHAR_UUID = bluetooth.UUID("19B10004-E8F2-537E-4F6Cg-D104768A1214")
HA_IP_CHAR_UUID = bluetooth.UUID("19B10004-E8F2-537E-4F6C-D104768A1214")

# BLE advertising name
DEVICE_NAME = "Pico-Switch"

# Store our BLE server instance
_server = None
_conn_handle = None
_service = None
_server_running = False


def _get_type_value():
    return "type: Smart Switch"


def _get_name_value():
    return "name: " + shared.config.value["name"] or DEVICE_NAME


def _get_layout_value():
    return "layout: " + shared.config.value["layout"]


def _get_version_value():
    return "version: " + str(shared.config.version)


def _get_ip_value():
    return "ip: " + shared.wifi.ip


def _get_ha_ip_value():
    return "ha-ip: " + shared.config.value["home-assistant-ip"]


async def ble_server_task():
    """Main BLE server task."""
    global _server, _conn_handle, _service, _server_running

    if _server_running:
        print("BLE server already running")
        return

    _server_running = True
    print("Starting BLE server")

    # Create a service
    _service = aioble.Service(DEVICE_SERVICE_UUID)

    # Create characteristics for each config value
    type_char = aioble.Characteristic(
        _service,
        TYPE_CHAR_UUID,
        read=True,
        notify=True,
    )

    name_char = aioble.Characteristic(
        _service,
        NAME_CHAR_UUID,
        read=True,
        notify=True,
    )

    layout_char = aioble.Characteristic(
        _service,
        LAYOUT_CHAR_UUID,
        read=True,
        notify=True,
    )

    version_char = aioble.Characteristic(
        _service,
        VERSION_CHAR_UUID,
        read=True,
        notify=True,
    )

    ip_char = aioble.Characteristic(
        _service,
        IP_CHAR_UUID,
        read=True,
        notify=True,
    )

    ha_ip_char = aioble.Characteristic(
        _service,
        HA_IP_CHAR_UUID,
        read=True,
        notify=True,
    )

    # Register service
    aioble.register_services(_service)

    # Set initial values for characteristics
    name_bytes = _get_name_value().encode()
    layout_bytes = _get_layout_value().encode()
    version_bytes = _get_version_value().encode()
    ip_bytes = _get_ip_value().encode()
    ha_ip_bytes = _get_ha_ip_value().encode()

    type_char.write(_get_type_value().encode())
    name_char.write(name_bytes)
    layout_char.write(layout_bytes)
    version_char.write(version_bytes)
    ip_char.write(ip_bytes)
    ha_ip_char.write(ha_ip_bytes)

    print("BLE services registered")

    try:
        """Start advertising our BLE service."""
        device_name = "Smart Switch (" + (shared.config.value["name"]
                                          or DEVICE_NAME) + ")"
        print(f"Starting BLE advertising as '{device_name}'")

        async with await aioble.advertise(
                interval_us=_ADV_INTERVAL_US,
                name=device_name,
                services=[DEVICE_SERVICE_UUID],
                timeout_ms=30000,
        ) as connection:
            print("Connection from", connection.device)
            await connection.disconnected(timeout_ms=None)
            print("Connection terminated")
    except Exception as e:
        print("BLE error:", e)
