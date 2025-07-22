import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.requestqueue.queue import RequestQueue
from app.requestqueue.request import Request


class TestRequestQueue(unittest.TestCase):

    def test_request_queue_init(self):
        queue = RequestQueue(5, "192.168.1.100")

        self.assertEqual(queue.max_size, 5)
        self.assertEqual(queue.host, "192.168.1.100")
        self.assertEqual(len(queue.queue), 0)
        self.assertEqual(queue.current_request, None)

    def test_add_request_to_empty_queue(self):
        queue = RequestQueue(5, "192.168.1.100")
        request = Request("test", "data")

        result = queue.add(request)

        self.assertTrue(result)
        self.assertEqual(len(queue.queue), 1)
        self.assertEqual(queue.queue[0], request)

    def test_add_request_to_full_queue(self):
        queue = RequestQueue(2, "192.168.1.100")

        queue.add(Request("test1", "data1"))
        queue.add(Request("test2", "data2"))

        result = queue.add(Request("test3", "data3"))

        self.assertFalse(result)
        self.assertEqual(len(queue.queue), 2)

    def test_get_next_request(self):
        queue = RequestQueue(5, "192.168.1.100")
        request1 = Request("test1", "data1")
        request2 = Request("test2", "data2")

        queue.add(request1)
        queue.add(request2)

        next_request = queue._get_next()

        self.assertEqual(next_request, request1)
        self.assertEqual(len(queue.queue), 1)
        self.assertEqual(queue.queue[0], request2)

    def test_get_next_request_empty_queue(self):
        queue = RequestQueue(5, "192.168.1.100")

        next_request = queue._get_next()

        self.assertIsNone(next_request)

    @patch('app.requestqueue.queue.urequests')
    def test_send_request_success(self, mock_urequests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_urequests.post.return_value = mock_response

        queue = RequestQueue(5, "192.168.1.100")
        request = Request("POST", '{"test": "data"}')
        success_callback = Mock()
        request.on_success = success_callback

        queue._send(request)

        mock_urequests.post.assert_called_once()
        success_callback.assert_called_once()

    @patch('app.requestqueue.queue.urequests')
    def test_send_request_failure(self, mock_urequests):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_urequests.post.return_value = mock_response

        queue = RequestQueue(5, "192.168.1.100")
        request = Request("POST", '{"test": "data"}')
        failure_callback = Mock()
        request.on_failure = failure_callback

        queue._send(request)

        mock_urequests.post.assert_called_once()
        failure_callback.assert_called_once()

    @patch('app.requestqueue.queue.urequests')
    def test_send_request_exception(self, mock_urequests):
        mock_urequests.post.side_effect = Exception("Network error")

        queue = RequestQueue(5, "192.168.1.100")
        request = Request("POST", '{"test": "data"}')
        failure_callback = Mock()
        request.on_failure = failure_callback

        with patch('builtins.print'):
            queue._send(request)

        failure_callback.assert_called_once()

    @patch('app.requestqueue.queue.urequests')
    def test_poll_with_no_current_request(self, mock_urequests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_urequests.post.return_value = mock_response

        queue = RequestQueue(5, "192.168.1.100")
        request = Request("POST", '{"test": "data"}')
        queue.add(request)

        queue.poll()

        self.assertIsNone(queue.current_request)
        mock_urequests.post.assert_called_once()

    def test_poll_with_current_request_in_progress(self):
        queue = RequestQueue(5, "192.168.1.100")
        request = Request("POST", '{"test": "data"}')
        queue.current_request = request

        with patch.object(queue, '_get_next') as mock_get_next:
            queue.poll()

        mock_get_next.assert_not_called()

    def test_poll_empty_queue(self):
        queue = RequestQueue(5, "192.168.1.100")

        with patch.object(queue, '_send') as mock_send:
            queue.poll()

        mock_send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
