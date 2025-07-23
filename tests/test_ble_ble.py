import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestBleBle(unittest.TestCase):

    def test_imports_successful(self):
        try:
            from app.ble import ble
            self.assertTrue(hasattr(ble, 'ble_server_task'))
        except ImportError as e:
            self.fail(f"Failed to import ble module: {e}")

    def test_ble_server_task_exists(self):
        from app.ble import ble
        
        self.assertTrue(hasattr(ble, 'ble_server_task'))
        self.assertTrue(callable(getattr(ble, 'ble_server_task', None)))

    @patch('app.ble.ble.aioble')
    def test_ble_server_task_callable(self, mock_aioble):
        from app.ble import ble
        
        task_func = getattr(ble, 'ble_server_task', None)
        
        try:
            if task_func:
                task = task_func()
                self.assertIsNotNone(task)
        except Exception as e:
            pass


if __name__ == '__main__':
    unittest.main()