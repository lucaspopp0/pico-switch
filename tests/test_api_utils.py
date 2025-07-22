import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.api import utils


class TestApiUtils(unittest.TestCase):

    def test_send_response_basic(self):
        mock_server = Mock()

        utils.send_response(mock_server, "Hello World")

        expected_calls = [
            unittest.mock.call("HTTP/1.0 200 Ok\r\n"),
            unittest.mock.call("Content type:text/html\r\n"),
            unittest.mock.call("\r\n"),
            unittest.mock.call("Hello World")
        ]

        mock_server.send.assert_has_calls(expected_calls)

    def test_send_response_custom_params(self):
        mock_server = Mock()

        utils.send_response(mock_server,
                            "Error",
                            http_code=404,
                            content_type="text/plain",
                            extend_headers=["Cache-Control: no-cache"])

        expected_calls = [
            unittest.mock.call("HTTP/1.0 404 Not found\r\n"),
            unittest.mock.call("Content type:text/plain\r\n"),
            unittest.mock.call("Cache-Control: no-cache\r\n"),
            unittest.mock.call("\r\n"),
            unittest.mock.call("Error")
        ]

        mock_server.send.assert_has_calls(expected_calls)

    def test_get_request_method(self):
        request = "GET /path HTTP/1.1\r\nHost: example.com\r\n"

        method = utils.get_request_method(request)

        self.assertEqual(method, "GET")

    def test_get_request_method_post(self):
        request = "POST /api HTTP/1.1\r\nHost: example.com\r\n"

        method = utils.get_request_method(request)

        self.assertEqual(method, "POST")

    def test_get_request_query_string_with_params(self):
        request = "GET /path?foo=bar&baz=qux HTTP/1.1\r\n"

        query_string = utils.get_request_query_string(request)

        self.assertEqual(query_string, "foo=bar&baz=qux")

    def test_get_request_query_string_no_params(self):
        request = "GET /path HTTP/1.1\r\n"

        query_string = utils.get_request_query_string(request)

        self.assertEqual(query_string, "")

    def test_parse_query_string_empty(self):
        result = utils.parse_query_string("")

        self.assertEqual(result, {})

    def test_parse_query_string_single_param(self):
        result = utils.parse_query_string("foo=bar")

        self.assertEqual(result, {"foo": "bar"})

    def test_parse_query_string_multiple_params(self):
        result = utils.parse_query_string("foo=bar&baz=qux")

        self.assertEqual(result, {"foo": "bar", "baz": "qux"})

    def test_parse_query_string_param_no_value(self):
        result = utils.parse_query_string("foo")

        self.assertEqual(result, {"foo": ""})

    def test_get_request_query_params(self):
        request = "GET /path?foo=bar&baz=qux HTTP/1.1\r\n"

        params = utils.get_request_query_params(request)

        self.assertEqual(params, {"foo": "bar", "baz": "qux"})

    def test_get_request_post_params_get_request(self):
        request = "GET /path HTTP/1.1\r\n"

        result = utils.get_request_post_params(request)

        self.assertIsNone(result)

    def test_get_request_post_params_post_with_data(self):
        request = "POST /api HTTP/1.1\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\nfoo=bar&baz=qux"

        result = utils.get_request_post_params(request)

        self.assertEqual(result, {"foo": "bar", "baz": "qux"})

    def test_get_request_post_params_post_no_data(self):
        request = "POST /api HTTP/1.1\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\n"

        result = utils.get_request_post_params(request)

        self.assertEqual(result, {})

    def test_unquote_no_encoding(self):
        result = utils.unquote("hello world")

        self.assertEqual(result, "hello world")

    def test_unquote_with_encoding(self):
        result = utils.unquote("hello%20world")

        self.assertEqual(result, "hello world")

    def test_unquote_empty_string(self):
        result = utils.unquote("")

        self.assertEqual(result, "")

    def test_unquote_none(self):
        result = utils.unquote(None)

        self.assertEqual(result, "")

    def test_unquote_bytes(self):
        result = utils.unquote(b"hello%20world")

        self.assertEqual(result, "hello world")

    def test_unquote_complex_encoding(self):
        result = utils.unquote("hello%2Bworld%3Dfoo")

        self.assertEqual(result, "hello+world=foo")

    def test_http_codes_constant(self):
        self.assertIn(200, utils.HTTP_CODES)
        self.assertEqual(utils.HTTP_CODES[200], 'Ok')
        self.assertIn(404, utils.HTTP_CODES)
        self.assertEqual(utils.HTTP_CODES[404], 'Not found')


if __name__ == '__main__':
    unittest.main()
