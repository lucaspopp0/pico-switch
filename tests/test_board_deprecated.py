import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestBoardDeprecated(unittest.TestCase):

    def test_imports_successful(self):
        try:
            from app.board import deprecated
            self.assertTrue(hasattr(deprecated, 'Routine'))
            self.assertTrue(hasattr(deprecated, 'Wheel'))
            self.assertTrue(hasattr(deprecated, 'Switch'))
        except ImportError as e:
            self.fail(f"Failed to import deprecated module: {e}")

    def test_routine_class_exists(self):
        from app.board import deprecated

        self.assertTrue(hasattr(deprecated, 'Routine'))
        self.assertTrue(callable(getattr(deprecated, 'Routine', None)))

    def test_wheel_class_exists(self):
        from app.board import deprecated

        self.assertTrue(hasattr(deprecated, 'Wheel'))
        self.assertTrue(callable(getattr(deprecated, 'Wheel', None)))

    def test_switch_class_exists(self):
        from app.board import deprecated

        self.assertTrue(hasattr(deprecated, 'Switch'))
        self.assertTrue(callable(getattr(deprecated, 'Switch', None)))


if __name__ == '__main__':
    unittest.main()
