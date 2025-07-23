import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.wifi.wifi import WiFiController


class TestWiFiController(unittest.TestCase):

    @patch('app.wifi.wifi.network.WLAN')
    def test_wifi_controller_init(self, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        controller = WiFiController("test_ssid", "test_password")
        
        self.assertEqual(controller._ssid, "test_ssid")
        self.assertEqual(controller._psk, "test_password")
        self.assertEqual(controller.wlan, mock_wlan)
        self.assertFalse(controller._connected)
        self.assertIsNone(controller._ip)
        self.assertFalse(controller._backoff)
        self.assertIsNone(controller._backoff_timer)
        self.assertIsNotNone(controller.on_connecting)
        self.assertIsNotNone(controller.on_connected)
        self.assertIsNotNone(controller.on_failed)

    @patch('app.wifi.wifi.network.WLAN')
    @patch('app.wifi.wifi.Timer')
    def test_connect_with_backoff_active(self, mock_timer_class, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        controller = WiFiController("test_ssid", "test_password")
        controller._backoff = True
        
        controller.connect()
        
        mock_timer_class.assert_not_called()

    @patch('app.wifi.wifi.network.WLAN')
    @patch('app.wifi.wifi.Timer')
    def test_connect_creates_backoff_timer(self, mock_timer_class, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer
        
        controller = WiFiController("test_ssid", "test_password")
        
        on_connecting_called = False
        def mock_on_connecting():
            nonlocal on_connecting_called
            on_connecting_called = True
        
        controller.on_connecting = mock_on_connecting
        
        controller.connect()
        
        self.assertTrue(controller._backoff)
        self.assertTrue(on_connecting_called)
        mock_timer_class.assert_called_once()

    @patch('app.wifi.wifi.network.WLAN')
    @patch('app.wifi.wifi.Timer')
    def test_connect_deinits_existing_timer(self, mock_timer_class, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        mock_existing_timer = Mock()
        mock_new_timer = Mock()
        mock_timer_class.return_value = mock_new_timer
        
        controller = WiFiController("test_ssid", "test_password")
        controller._backoff_timer = mock_existing_timer
        
        controller.connect()
        
        mock_existing_timer.deinit.assert_called_once()

    @patch('app.wifi.wifi.network.WLAN')
    def test_connect_backoff_timer_callback(self, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        controller = WiFiController("test_ssid", "test_password")
        
        with patch('app.wifi.wifi.Timer') as mock_timer_class:
            mock_timer = Mock()
            mock_timer_class.return_value = mock_timer
            
            controller.connect()
            
            callback = mock_timer_class.call_args[1]['callback']
            callback(None)
            
            self.assertFalse(controller._backoff)

    @patch('app.wifi.wifi.network.WLAN')
    def test_on_connecting_callback(self, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        controller = WiFiController("test_ssid", "test_password")
        controller.on_connecting = test_callback
        
        with patch('app.wifi.wifi.Timer'):
            controller.connect()
        
        self.assertTrue(callback_called)

    @patch('app.wifi.wifi.network.WLAN')
    def test_on_connected_callback(self, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        controller = WiFiController("test_ssid", "test_password")
        controller.on_connected = test_callback
        
        controller.on_connected()
        
        self.assertTrue(callback_called)

    @patch('app.wifi.wifi.network.WLAN')
    def test_on_failed_callback(self, mock_wlan_class):
        mock_wlan = Mock()
        mock_wlan_class.return_value = mock_wlan
        
        controller = WiFiController("test_ssid", "test_password")
        
        try:
            controller.on_failed("test failure")
        except Exception as e:
            self.fail(f"on_failed callback should not raise exception: {e}")


if __name__ == '__main__':
    unittest.main()