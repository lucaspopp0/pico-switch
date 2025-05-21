import asyncio
import aioble
import bluetooth
from ubluetooth import UUID
import struct
import ujson
from . import config

# Service UUID for our device (custom UUID for Pico-Switch)
DEVICE_SERVICE_UUID = bluetooth.UUID("19B10000-E8F2-537E-4F6C-D104768A1214")

# Characteristic UUIDs for our device
NAME_CHAR_UUID = bluetooth.UUID("19B10001-E8F2-537E-4F6C-D104768A1214")
LAYOUT_CHAR_UUID = bluetooth.UUID("19B10002-E8F2-537E-4F6C-D104768A1214")
VERSION_CHAR_UUID = bluetooth.UUID("19B10003-E8F2-537E-4F6C-D104768A1214")
HA_IP_CHAR_UUID = bluetooth.UUID("19B10004-E8F2-537E-4F6C-D104768A1214")

# BLE advertising name
DEVICE_NAME = "Pico-Switch"

# Store our BLE server instance
_server = None
_conn_handle = None
_service = None

def _get_name_value():
    return str(config.value.get("name", "Pico-Switch"))

def _get_layout_value():
    return str(config.value.get("layout", ""))

def _get_version_value():
    return str(config.version)

def _get_ha_ip_value():
    return str(config.value.get("home-assistant-ip", ""))

async def _start_advertising():
    """Start advertising our BLE service."""
    device_name = _get_name_value() or DEVICE_NAME
    print(f"Starting BLE advertising as '{device_name}'")
    
    # Create advertisement with device name and service UUID
    adv = aioble.Advertisement(
        name=device_name,
        services=[DEVICE_SERVICE_UUID],
    )
    
    # Start advertising
    await aioble.advertise(adv, interval_us=500000, timeout_ms=0)

async def _ble_server_task():
    """Main BLE server task."""
    global _server, _conn_handle, _service
    
    # Create a service
    _service = aioble.Service(DEVICE_SERVICE_UUID)
    
    # Create characteristics for each config value
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
    ha_ip_bytes = _get_ha_ip_value().encode()
    
    await name_char.write(name_bytes)
    await layout_char.write(layout_bytes)
    await version_char.write(version_bytes)
    await ha_ip_char.write(ha_ip_bytes)
    
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

def start_ble_server():
    """Initialize and start the BLE server in a background task."""
    loop = asyncio.get_event_loop()
    loop.create_task(_ble_server_task())
    print("BLE server started in background")