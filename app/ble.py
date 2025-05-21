import asyncio
import aioble
import bluetooth
from ubluetooth import UUID
import struct
import ujson
from . import config, wifi

_ADV_INTERVAL_US = 250000

# Service UUID for our device (custom UUID for Pico-Switch)
DEVICE_SERVICE_UUID = bluetooth.UUID("19B10000-E8F2-537E-4F6C-D104768A1214")

# Characteristic UUIDs for our device
TYPE_CHAR_UUID = bluetooth.UUID("19B10001-E8F2-537E-4F6C-D104768A1214")
NAME_CHAR_UUID = bluetooth.UUID("19B10001-E8F2-537E-4F6C-D104768A1214")
LAYOUT_CHAR_UUID = bluetooth.UUID("19B10002-E8F2-537E-4F6C-D104768A1214")
VERSION_CHAR_UUID = bluetooth.UUID("19B10003-E8F2-537E-4F6C-D104768A1214")
IP_CHAR_UUID = bluetooth.UUID("19B10004-E8F2-537E-4F6C-D104768A1214")
HA_IP_CHAR_UUID = bluetooth.UUID("19B10004-E8F2-537E-4F6C-D104768A1214")

# BLE advertising name
DEVICE_NAME = "Pico-Switch"

# Store our BLE server instance
_server = None
_conn_handle = None
_service = None

def _get_type_value():
    return "type: Smart Switch"

def _get_name_value():
    return "name: " + config.value["name"] or DEVICE_NAME

def _get_layout_value():
    return "layout: " + config.value["layout"]

def _get_version_value():
    return "version: " + str(config.version)

def _get_ip_value():
    return "ip: " + wifi.current_ip

def _get_ha_ip_value():
    return "ha-ip: " + config.value["home-assistant-ip"]

async def _start_advertising():
    """Start advertising our BLE service."""
    device_name = _get_name_value() or DEVICE_NAME
    print(f"Starting BLE advertising as '{device_name}'")
    
    await aioble.advertise(
        interval_us=_ADV_INTERVAL_US,
        name=device_name,
        services=[DEVICE_SERVICE_UUID],
        timeout_ms=0,
    )

async def _ble_server_task():
    """Main BLE server task."""
    global _server, _conn_handle, _service
    
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
    
    # Start advertising
    await _start_advertising()
    
    # Main connection loop
    while True:
        try:
            # Wait for a connection
            connection = await aioble.wait_for_connection()
            print("BLE client connected:", connection.device)
            _conn_handle = connection
            
            try:
                # Wait for disconnection
                await connection.disconnected()
            finally:
                print("BLE client disconnected")
                _conn_handle = None
                
                # Resume advertising after disconnection
                await _start_advertising()
        except Exception as e:
            print("BLE error:", e)
            # Brief delay before retrying
            await asyncio.sleep(1)

async def start_ble_server():
    """Initialize and start the BLE server in a background task."""
    asyncio.run(_ble_server_task())
    print("BLE server started in background")