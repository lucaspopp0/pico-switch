import network
import time
from machine import Timer


class WiFiController:

    def __init__(
        self,
        ssid: str,
        psk: str,
    ):
        # Store the network config
        self._ssid = ssid
        self._psk = psk

        self.wlan = network.WLAN(network.STA_IF)
        self._connected = False
        self._ip: str | None = None

        self._backoff = False
        self._backoff_timer = None

        self.on_connecting = lambda: None
        self.on_connected = lambda: None

        def on_failed(failure: str):
            pass

        self.on_failed = on_failed

    def connect(self):
        if self._backoff:
            return

        if self._backoff_timer is not None:
            self._backoff_timer.deinit()

        def back_off(_):
            self._backoff = False

        self._backoff = True
        self._backoff_timer = Timer(
            -1,
            mode=Timer.ONE_SHOT,
            period=30000,
            callback=back_off,
        )

        self.on_connecting()

        self.wlan.active(True)
        self.wlan.connect(
            self._ssid,
            self._psk,
        )

        # Wait up to 10s for a successful connection
        wait = 10
        while 0 < wait:
            wait -= 1

            status = self.wlan.status()

            if status == network.STAT_GOT_IP:
                self._connected = True
                self.ip = self.wlan.ifconfig()[0]
                print('WiFi connected! (' + self.ip + ')')
                self.on_connected()
                return

            elif status == network.STAT_NO_AP_FOUND:
                self.on_failed('Failed to connect to "' + self._ssid +
                               '" not', )
                return

            elif status == network.STAT_WRONG_PASSWORD:
                self.on_failed('WiFi connection failed: Wrong password', )
                return

            elif status == network.STAT_CONNECT_FAIL:
                self.on_failed('WiFi connection failed', )
                return

            else:
                print('Trying to connect to "' + self._ssid + '"...')
                time.sleep(1)

        self.on_failed('WiFi connection timed out after 10s', )
