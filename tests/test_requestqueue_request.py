import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.requestqueue.request import Request


class TestRequest(unittest.TestCase):

    def test_request_init(self):
        request = Request("test_type", "test_data")
        
        self.assertEqual(request.type, "test_type")
        self.assertEqual(request.data, "test_data")
        self.assertIsNotNone(request.on_success)
        self.assertIsNotNone(request.on_failure)

    def test_request_init_with_callbacks(self):
        success_callback = Mock()
        failure_callback = Mock()
        
        request = Request("test_type", "test_data", success_callback, failure_callback)
        
        self.assertEqual(request.on_success, success_callback)
        self.assertEqual(request.on_failure, failure_callback)

    def test_request_default_callbacks_callable(self):
        request = Request("test_type", "test_data")
        
        try:
            request.on_success()
            request.on_failure()
        except Exception as e:
            self.fail(f"Default callbacks should be callable: {e}")

    def test_request_str_representation(self):
        request = Request("POST", '{"key": "value"}')
        
        str_repr = str(request)
        
        self.assertIn("POST", str_repr)
        self.assertIn('{"key": "value"}', str_repr)


if __name__ == '__main__':
    unittest.main()