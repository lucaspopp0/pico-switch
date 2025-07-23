import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.board import layouts


class TestBoardLayouts(unittest.TestCase):

    def test_v3_layout_constant(self):
        self.assertEqual(layouts.V3, "v3")

    def test_v4_layout_constant(self):
        self.assertEqual(layouts.V4, "v4")

    def test_v5_layout_constant(self):
        self.assertEqual(layouts.V5, "v5")

    def test_v6_layout_constant(self):
        self.assertEqual(layouts.V6, "v6")

    def test_v7_layout_constant(self):
        self.assertEqual(layouts.V7, "v7")

    def test_v8_layout_constant(self):
        self.assertEqual(layouts.V8, "v8")

    def test_v9_layout_constant(self):
        self.assertEqual(layouts.V9, "v9")

    def test_all_layouts_are_strings(self):
        layouts_list = [
            layouts.V3, layouts.V4, layouts.V5, layouts.V6, layouts.V7,
            layouts.V8, layouts.V9
        ]

        for layout in layouts_list:
            self.assertIsInstance(layout, str)

    def test_all_layouts_are_unique(self):
        layouts_list = [
            layouts.V3, layouts.V4, layouts.V5, layouts.V6, layouts.V7,
            layouts.V8, layouts.V9
        ]

        self.assertEqual(len(layouts_list), len(set(layouts_list)))


if __name__ == '__main__':
    unittest.main()
