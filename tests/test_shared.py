import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import shared


class TestShared(unittest.TestCase):

    def setUp(self):
        shared.config = None
        shared.requestqueue = None
        shared.board = None
        shared.wifi = None
        shared.api = None

    @patch('app.shared.Config')
    def test_setup_config(self, mock_config_class):
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        shared.setup_config()
        
        mock_config_class.assert_called_once()
        mock_config.load.assert_called_once()
        self.assertEqual(shared.config, mock_config)

    @patch('app.shared.RequestQueue')
    def test_setup_request_queue(self, mock_queue_class):
        mock_config = Mock()
        mock_config.value = {'homeassistant-ip': '192.168.1.100'}
        shared.config = mock_config
        
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        shared.setup_request_queue()
        
        mock_queue_class.assert_called_once_with(5, '192.168.1.100')
        self.assertEqual(shared.requestqueue, mock_queue)

    @patch('app.shared.BasicButtonBoard')
    @patch('app.shared.basics')
    @patch('app.shared.layouts')
    def test_setup_board_v3(self, mock_layouts, mock_basics, mock_board_class):
        mock_config = Mock()
        mock_config.value = {'layout': 'v3'}
        shared.config = mock_config
        
        mock_layouts.V3 = 'v3'
        mock_led = Mock()
        mock_basics.RgbLED.return_value = mock_led
        mock_button = Mock()
        mock_basics.PushButton.return_value = mock_button
        
        mock_board = Mock()
        mock_board_class.return_value = mock_board
        
        shared.setup_board()
        
        mock_basics.RgbLED.assert_called_with(18, 17, 16)
        self.assertEqual(shared.board, mock_board)

    @patch('app.shared.WiFiController')
    def test_setup_wifi(self, mock_wifi_class):
        mock_config = Mock()
        mock_config.value.get_wifi.return_value = ('test_ssid', 'test_password', True)
        shared.config = mock_config
        
        mock_board = Mock()
        shared.board = mock_board
        
        mock_wifi = Mock()
        mock_wifi_class.return_value = mock_wifi
        
        shared.setup_wifi()
        
        mock_wifi_class.assert_called_once_with('test_ssid', 'test_password')
        self.assertEqual(shared.wifi, mock_wifi)
        self.assertEqual(mock_wifi.on_connecting, mock_board.on_wifi_connecting)
        self.assertEqual(mock_wifi.on_connected, mock_board.on_wifi_connected)
        self.assertEqual(mock_wifi.on_failed, mock_board.on_wifi_failed)

    def test_setup_wifi_no_config(self):
        mock_config = Mock()
        mock_config.value.get_wifi.return_value = (None, None, False)
        shared.config = mock_config
        
        shared.setup_wifi()
        
        self.assertIsNone(shared.wifi)

    def test_setup_bluetooth(self):
        mock_board = Mock()
        shared.board = mock_board
        
        shared.setup_bluetooth()
        
        self.assertIsNotNone(mock_board.on_pair)
        self.assertIsNotNone(mock_board.on_pair_cancel)

    @patch('app.shared.update_manager')
    def test_setup_automatic_updates(self, mock_update_manager):
        mock_board = Mock()
        shared.board = mock_board
        
        shared.setup_automatic_updates()
        
        self.assertEqual(mock_board.on_update, mock_update_manager.try_update)

    @patch('app.shared.server.Server')
    @patch('app.shared.routes.setup_routes')
    def test_setup_api(self, mock_setup_routes, mock_server_class):
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        
        shared.setup_api()
        
        mock_server_class.assert_called_once()
        mock_setup_routes.assert_called_once_with(mock_server)
        self.assertEqual(shared.api, mock_server)


if __name__ == '__main__':
    unittest.main()