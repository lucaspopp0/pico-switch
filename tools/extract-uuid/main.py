"""
Extract and print the unique UUID of a Raspberry Pi Pico W board.
This uses the same method as the main pico-switch firmware.
"""

import machine
import ubinascii


def get_device_uuid() -> str:
    """Display the hexadecimal representation of the device's UID"""
    uid_bytes = machine.unique_id()
    uid = ubinascii.hexlify(uid_bytes).decode()
    return uid


uuid = get_device_uuid()
print(f"Device UUID: {uuid}")
