import unittest

from app.wifi.wifi import WiFiController


class TestWiFi(unittest.TestCase):

    def test_connect(self):
        """Dummy test"""
        _ = WiFiController("ssid", "psk")
