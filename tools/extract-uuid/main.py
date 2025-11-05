"""
Extract and print the unique UUID of a Raspberry Pi Pico W board.
This uses the same method as the main pico-switch firmware.
"""

import machine
import ubinascii


def get_device_uuid() -> str:
    """Return the device UUID as an uppercase hexadecimal string"""
    uid_bytes = machine.unique_id()
    return ubinascii.hexlify(uid_bytes).decode().upper()


uuid = get_device_uuid()
print(f"Device UUID: {uuid}")
