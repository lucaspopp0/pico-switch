import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.api import routes


class TestApiRoutes(unittest.TestCase):

    @patch('app.api.routes.config')
    def test_get_info(self, mock_config):
        mock_config.info.return_value = '{"status": "ok"}'
        mock_server = Mock()

        routes.get_info(mock_server)

        expected_calls = [
            unittest.mock.call("HTTP/1.0 200 OK\r\n"),
            unittest.mock.call("Content-Type: application/json\r\n\r\n"),
            unittest.mock.call('{"status": "ok"}')
        ]

        mock_server.send.assert_has_calls(expected_calls)
        mock_config.info.assert_called_once()

    def test_setup_routes(self):
        mock_server = Mock()

        routes.setup_routes(mock_server)

        mock_server.add_route.assert_called_once()
        call_args = mock_server.add_route.call_args
        self.assertEqual(call_args[1]['path'], '/info')
        self.assertIsNotNone(call_args[1]['handler'])

    def test_info_route_handler(self):
        mock_server = Mock()

        routes.setup_routes(mock_server)

        handler = mock_server.add_route.call_args[1]['handler']

        with patch.object(routes, 'get_info') as mock_get_info:
            handler(None)
            mock_get_info.assert_called_once_with(mock_server)


if __name__ == '__main__':
    unittest.main()
