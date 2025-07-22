import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app import start


class TestStart(unittest.TestCase):

    @patch('app.start.shared')
    @patch('app.start.update_manager')
    def test_start_success(self, mock_update_manager, mock_shared):
        mock_shared.wifi._connected = True
        mock_update_manager.should_check_update.return_value = False
        
        with patch('builtins.print'):
            with self.assertRaises(KeyboardInterrupt):
                with patch('builtins.input', side_effect=KeyboardInterrupt):
                    start.start()
        
        mock_shared.setup_config.assert_called_once()
        mock_shared.setup_request_queue.assert_called_once()
        mock_shared.setup_board.assert_called_once()
        mock_shared.setup_wifi.assert_called_once()
        mock_shared.setup_bluetooth.assert_called_once()
        mock_shared.setup_automatic_updates.assert_called_once()
        mock_shared.setup_api.assert_called_once()
        mock_shared.wifi.connect.assert_called()
        mock_shared.api.start.assert_called_once()

    @patch('app.start.shared')
    @patch('app.start.update_manager')  
    def test_start_wifi_not_connected(self, mock_update_manager, mock_shared):
        mock_shared.wifi._connected = False
        
        result = start.start()
        
        mock_shared.setup_config.assert_called_once()
        mock_shared.setup_request_queue.assert_called_once()
        mock_shared.setup_board.assert_called_once()
        mock_shared.setup_wifi.assert_called_once()
        mock_shared.setup_bluetooth.assert_called_once()
        mock_shared.setup_automatic_updates.assert_called_once()
        mock_shared.setup_api.assert_called_once()
        mock_shared.wifi.connect.assert_called_once()
        mock_shared.api.start.assert_not_called()
        self.assertIsNone(result)

    @patch('app.start.shared')
    @patch('app.start.update_manager')
    def test_start_with_update_check(self, mock_update_manager, mock_shared):
        mock_shared.wifi._connected = True
        call_count = 0
        
        def mock_should_check():
            nonlocal call_count
            call_count += 1
            return call_count == 1
        
        mock_update_manager.should_check_update.side_effect = mock_should_check
        
        with patch('builtins.print'):
            with self.assertRaises(KeyboardInterrupt):
                with patch('builtins.input', side_effect=[None, KeyboardInterrupt]):
                    start.start()
        
        mock_update_manager.try_update.assert_called()

    @patch('app.start.shared')
    @patch('app.start.update_manager')
    def test_start_wifi_reconnection(self, mock_update_manager, mock_shared):
        call_count = 0
        
        def mock_connected():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True
            elif call_count == 2:
                return False
            else:
                return True
        
        mock_shared.wifi._connected = mock_connected
        mock_update_manager.should_check_update.return_value = False
        
        with patch('builtins.print'):
            with self.assertRaises(KeyboardInterrupt):
                with patch('builtins.input', side_effect=[None, None, KeyboardInterrupt]):
                    start.start()
        
        self.assertGreater(mock_shared.wifi.connect.call_count, 1)


if __name__ == '__main__':
    unittest.main()