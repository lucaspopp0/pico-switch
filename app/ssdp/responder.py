import socket
import struct
import select


def _ip_to_bytes(ip_string: str) -> bytes:
    """
    Convert an IP address string to bytes for multicast membership.

    This is needed because MicroPython's socket module doesn't have inet_aton().

    Example:
        '239.255.255.250' -> b'\xef\xff\xff\xfa'

    Args:
        ip_string: IP address as string (e.g., '239.255.255.250')

    Returns:
        bytes: 4-byte representation of the IP address
    """
    return bytes(map(int, ip_string.split('.')))


class SSDPResponder:
    """
    Lightweight SSDP responder for device discovery.
    Listens for M-SEARCH requests and responds with device information.
    """

    MULTICAST_ADDR = '239.255.255.250'
    SSDP_PORT = 1900
    DEVICE_TYPE = 'urn:schemas-lucaspopp0:device:SmartSwitch:1'

    def __init__(self, device_uuid: str, device_ip: str, device_version: str):
        """
        Initialize SSDP responder.

        Args:
            device_uuid: Unique device identifier
            device_ip: IP address of this device
            device_version: Firmware version
        """
        self.device_uuid = device_uuid
        self.device_ip = device_ip
        self.device_version = device_version
        self.sock = None
        self.poller = None

    def start(self):
        """Start the SSDP responder by creating and binding socket."""
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to SSDP port
        self.sock.bind(('', self.SSDP_PORT))

        # Join multicast group to receive SSDP discovery packets
        # IP_ADD_MEMBERSHIP requires: 4 bytes (multicast IP) + 4 bytes (interface, 0=any)
        multicast_bytes = _ip_to_bytes(self.MULTICAST_ADDR)
        mreq = struct.pack('4sl', multicast_bytes, 0)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # Set non-blocking mode
        self.sock.setblocking(False)

        # Create poller for non-blocking operation
        self.poller = select.poll()
        self.poller.register(self.sock, select.POLLIN)

        print(f"SSDP responder started on {self.MULTICAST_ADDR}:{self.SSDP_PORT}")

    def stop(self):
        """Stop the SSDP responder and close socket."""
        if self.poller:
            self.poller.unregister(self.sock)
        if self.sock:
            self.sock.close()
        print("SSDP responder stopped")

    def poll(self, timeout_ms: int = 0):
        """
        Poll for incoming M-SEARCH requests and respond if matching.

        Args:
            timeout_ms: Polling timeout in milliseconds (0 = non-blocking)
        """
        if not self.sock or not self.poller:
            return

        # Check for incoming data
        events = self.poller.poll(timeout_ms)
        if not events:
            return

        try:
            # Receive M-SEARCH request
            data, addr = self.sock.recvfrom(1024)
            message = data.decode('utf-8')

            # Parse M-SEARCH request
            if self._is_matching_search(message):
                print(f"SSDP M-SEARCH from {addr[0]}:{addr[1]}")
                self._send_response(addr)

        except Exception as e:
            print(f"SSDP error: {e}")

    def _is_matching_search(self, message: str) -> bool:
        """
        Check if M-SEARCH request matches our device type.

        Args:
            message: Raw M-SEARCH message

        Returns:
            True if we should respond to this search
        """
        if 'M-SEARCH' not in message:
            return False

        # Extract ST (Search Target) header
        for line in message.split('\r\n'):
            if line.startswith('ST:') or line.startswith('st:'):
                st_value = line.split(':', 1)[1].strip()

                # Respond to these search targets
                if st_value in ['ssdp:all', self.DEVICE_TYPE]:
                    return True

        return False

    def _send_response(self, addr: tuple):
        """
        Send SSDP response to requester.

        Args:
            addr: (ip, port) tuple of requester
        """
        location = f"http://{self.device_ip}/device.xml"
        usn = f"uuid:{self.device_uuid}::{self.DEVICE_TYPE}"

        response = (
            "HTTP/1.1 200 OK\r\n"
            "CACHE-CONTROL: max-age=1800\r\n"
            "EXT:\r\n"
            f"LOCATION: {location}\r\n"
            f"SERVER: MicroPython/1.20 PicoSwitch/{self.device_version}\r\n"
            f"ST: {self.DEVICE_TYPE}\r\n"
            f"USN: {usn}\r\n"
            "\r\n"
        )

        try:
            # Send unicast response to requester
            self.sock.sendto(response.encode('utf-8'), addr)
            print(f"SSDP response sent to {addr[0]}:{addr[1]}")
        except Exception as e:
            print(f"Failed to send SSDP response: {e}")

    def get_socket(self):
        """Return the underlying socket for polling integration."""
        return self.sock
