import bluetooth
from micropython import const
import ubinascii
import machine
from . import config

# BLE Constants
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_APPEARANCE = const(0x19)
_ADV_TYPE_MANUFACTURER = const(0xFF)

# Service UUIDs
_DEVICE_INFO_SERVICE_UUID = const(0x180A)
_PICO_SWITCH_SERVICE_UUID = bluetooth.UUID("e0ff0000-6588-4fca-8c8c-c80916b9be05")

# BLE Flags
_ADV_FLAGS = const(0x06)  # General Discoverable Mode | BR/EDR Not Supported

# Initialize BLE
ble = None
active = False

def init():
    """Initialize the BLE module."""
    global ble, active
    
    if ble is not None:
        return
    
    try:
        ble = bluetooth.BLE()
        active = True
        print("BLE initialized")
    except Exception as e:
        print("Failed to initialize BLE:", e)
        active = False

def is_active():
    """Check if BLE is active."""
    return active

def encode_name(name):
    """Encode the device name for BLE advertising."""
    name_bytes = name.encode()
    return bytes([len(name_bytes) + 1, _ADV_TYPE_NAME]) + name_bytes

def encode_services(uuid_list):
    """Encode a list of 16-bit service UUIDs for BLE advertising."""
    encoded = bytearray([len(uuid_list) * 2 + 1, _ADV_TYPE_UUID16_COMPLETE])
    for uuid in uuid_list:
        encoded.extend(bluetooth.pack_int(uuid, 2))
    return encoded

def encode_manufacturer_data(company_id, data):
    """Encode manufacturer specific data for BLE advertising."""
    encoded = bytearray([len(data) + 3, _ADV_TYPE_MANUFACTURER])
    encoded.extend(bluetooth.pack_int(company_id, 2))
    encoded.extend(data)
    return encoded

def start_advertising():
    """Start BLE advertising with device information."""
    global ble, active
    
    if not active or ble is None:
        init()
        if not active:
            return False
    
    # Generate device name with unique ID
    device_id = ubinascii.hexlify(machine.unique_id()).decode()[-4:]
    device_name = f"PicoSwitch-{device_id}"
    
    # Prepare advertising data
    payload = bytearray()
    
    # Add flags
    payload.extend(bytes([2, _ADV_TYPE_FLAGS, _ADV_FLAGS]))
    
    # Add device name
    payload.extend(encode_name(device_name))
    
    # Add service UUIDs
    payload.extend(encode_services([_DEVICE_INFO_SERVICE_UUID]))
    
    # Add manufacturer data: version and other info
    mfg_data = bytearray()
    # Company ID (using a generic test value, replace with your assigned ID)
    company_id = 0xFFFF
    
    # Add version info
    if config.version:
        version_str = config.version.encode()
        mfg_data.extend(bytes([len(version_str)]) + version_str)
    
    payload.extend(encode_manufacturer_data(company_id, mfg_data))
    
    # Start advertising
    try:
        ble.gap_advertise(100000, adv_data=payload)
        print(f"BLE advertising started as '{device_name}'")
        return True
    except Exception as e:
        print("Failed to start advertising:", e)
        return False

def stop_advertising():
    """Stop BLE advertising."""
    global ble, active
    
    if not active or ble is None:
        return
    
    try:
        ble.gap_advertise(None)
        print("BLE advertising stopped")
    except Exception as e:
        print("Failed to stop advertising:", e)