import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.api import server


class TestApiServer(unittest.TestCase):

    def test_server_init(self):
        srv = server.Server()
        
        self.assertEqual(srv._host, "0.0.0.0")
        self.assertEqual(srv._port, 80)
        self.assertEqual(srv._routes, [])
        self.assertIsNone(srv._connect)
        self.assertIsNone(srv._on_request_handler)
        self.assertIsNone(srv._on_not_found_handler)
        self.assertIsNone(srv._on_error_handler)
        self.assertIsNone(srv._sock)
        self.assertFalse(srv.on)

    def test_server_init_custom(self):
        srv = server.Server("localhost", 8080)
        
        self.assertEqual(srv._host, "localhost")
        self.assertEqual(srv._port, 8080)

    @patch('app.api.server.socket')
    def test_start(self, mock_socket_module):
        mock_sock = Mock()
        mock_socket_module.socket.return_value = mock_sock
        
        srv = server.Server()
        
        with patch('builtins.print'):
            srv.start()
        
        self.assertTrue(srv.on)
        mock_socket_module.socket.assert_called_once_with(mock_socket_module.AF_INET, mock_socket_module.SOCK_STREAM)
        mock_sock.setsockopt.assert_called_once_with(mock_socket_module.SOL_SOCKET, mock_socket_module.SO_REUSEADDR, 1)
        mock_sock.bind.assert_called_once_with(("0.0.0.0", 80))
        mock_sock.listen.assert_called_once_with(1)

    def test_add_route_default_method(self):
        srv = server.Server()
        handler = Mock()
        
        srv.add_route("/test", handler)
        
        self.assertEqual(len(srv._routes), 1)
        self.assertEqual(srv._routes[0]["path"], "/test")
        self.assertEqual(srv._routes[0]["handler"], handler)
        self.assertEqual(srv._routes[0]["method"], "GET")

    def test_add_route_custom_method(self):
        srv = server.Server()
        handler = Mock()
        
        srv.add_route("/test", handler, "POST")
        
        self.assertEqual(len(srv._routes), 1)
        self.assertEqual(srv._routes[0]["method"], "POST")

    def test_send_no_connection(self):
        srv = server.Server()
        
        with self.assertRaises(Exception) as context:
            srv.send("test data")
        
        self.assertIn("Can't send response, no connection instance", str(context.exception))

    def test_send_with_connection(self):
        srv = server.Server()
        mock_connection = Mock()
        srv._connect = mock_connection
        
        srv.send("test data")
        
        mock_connection.sendall.assert_called_once_with(b"test data")

    def test_find_route_exact_match(self):
        srv = server.Server()
        handler = Mock()
        srv.add_route("/test", handler)
        
        request = "GET /test HTTP/1.1\r\n"
        route = srv.find_route(request)
        
        self.assertIsNotNone(route)
        self.assertEqual(route["path"], "/test")
        self.assertEqual(route["handler"], handler)

    def test_find_route_no_match(self):
        srv = server.Server()
        handler = Mock()
        srv.add_route("/test", handler)
        
        request = "GET /other HTTP/1.1\r\n"
        route = srv.find_route(request)
        
        self.assertIsNone(route)

    def test_find_route_method_mismatch(self):
        srv = server.Server()
        handler = Mock()
        srv.add_route("/test", handler, "POST")
        
        request = "GET /test HTTP/1.1\r\n"
        route = srv.find_route(request)
        
        self.assertIsNone(route)

    def test_get_request(self):
        srv = server.Server()
        mock_connection = Mock()
        mock_connection.recv.return_value = b"test request"
        srv._connect = mock_connection
        
        result = srv.get_request()
        
        self.assertEqual(result, "test request")
        mock_connection.recv.assert_called_once_with(4096)

    def test_on_request(self):
        srv = server.Server()
        handler = Mock()
        
        srv.on_request(handler)
        
        self.assertEqual(srv._on_request_handler, handler)

    def test_on_not_found(self):
        srv = server.Server()
        handler = Mock()
        
        srv.on_not_found(handler)
        
        self.assertEqual(srv._on_not_found_handler, handler)

    def test_on_error(self):
        srv = server.Server()
        handler = Mock()
        
        srv.on_error(handler)
        
        self.assertEqual(srv._on_error_handler, handler)

    def test_route_not_found_custom_handler(self):
        srv = server.Server()
        mock_handler = Mock()
        srv._on_not_found_handler = mock_handler
        
        srv._route_not_found("test request")
        
        mock_handler.assert_called_once_with("test request")

    def test_route_not_found_default_handler(self):
        srv = server.Server()
        mock_connection = Mock()
        srv._connect = mock_connection
        
        srv._route_not_found("test request")
        
        expected_calls = [
            unittest.mock.call(b"HTTP/1.0 404 Not Found\r\n"),
            unittest.mock.call(b"Content-Type: text/plain\r\n\r\n"),
            unittest.mock.call(b"Not found")
        ]
        
        mock_connection.sendall.assert_has_calls(expected_calls)

    def test_internal_error_custom_handler(self):
        srv = server.Server()
        mock_handler = Mock()
        srv._on_error_handler = mock_handler
        error = Exception("test error")
        
        srv._internal_error(error)
        
        mock_handler.assert_called_once_with(error)

    @patch('app.api.server.sys')
    def test_internal_error_default_handler_with_print_exception(self, mock_sys):
        srv = server.Server()
        mock_connection = Mock()
        srv._connect = mock_connection
        
        mock_output = Mock()
        mock_output.getvalue.return_value = "exception traceback"
        mock_sys.print_exception = Mock()
        
        with patch('app.api.server.io.StringIO', return_value=mock_output):
            with patch('builtins.print'):
                srv._internal_error(Exception("test error"))
        
        expected_calls = [
            unittest.mock.call(b"HTTP/1.0 500 Internal Server Error\r\n"),
            unittest.mock.call(b"Content-Type: text/plain\r\n\r\n"),
            unittest.mock.call(b"Error: exception traceback")
        ]
        
        mock_connection.sendall.assert_has_calls(expected_calls)

    @patch('app.api.server.sys')
    def test_internal_error_default_handler_no_print_exception(self, mock_sys):
        srv = server.Server()
        mock_connection = Mock()
        srv._connect = mock_connection
        
        del mock_sys.print_exception
        error = Exception("test error")
        
        with patch('builtins.print'):
            srv._internal_error(error)
        
        expected_calls = [
            unittest.mock.call(b"HTTP/1.0 500 Internal Server Error\r\n"),
            unittest.mock.call(b"Content-Type: text/plain\r\n\r\n"),
            unittest.mock.call(b"Error: test error")
        ]
        
        mock_connection.sendall.assert_has_calls(expected_calls)


if __name__ == '__main__':
    unittest.main()