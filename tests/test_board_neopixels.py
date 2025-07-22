import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestBoardNeopixels(unittest.TestCase):

    def test_pixel_coords_init(self):
        from app.board.neopixels import PixelCoords
        
        coords = PixelCoords(chain=1, offset=3)
        
        self.assertEqual(coords.chain, 1)
        self.assertEqual(coords.offset, 3)

    @patch('app.board.neopixels.NeoPixel')
    @patch('app.board.neopixels.Pin')
    def test_neopixels_init(self, mock_pin_class, mock_neopixel_class):
        from app.board.neopixels import NeoPixels
        
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_neopixel = Mock()
        mock_neopixel_class.return_value = mock_neopixel
        
        pixels = NeoPixels()
        
        self.assertEqual(len(pixels.rows), 4)
        self.assertEqual(mock_neopixel_class.call_count, 4)
        
        expected_pin_calls = [
            unittest.mock.call(0),
            unittest.mock.call(4),
            unittest.mock.call(22),
            unittest.mock.call(18)
        ]
        mock_pin_class.assert_has_calls(expected_pin_calls)
        
        expected_neopixel_calls = [
            unittest.mock.call(mock_pin, 6),
            unittest.mock.call(mock_pin, 4),
            unittest.mock.call(mock_pin, 6),
            unittest.mock.call(mock_pin, 4)
        ]
        mock_neopixel_class.assert_has_calls(expected_neopixel_calls)

    @patch('app.board.neopixels.NeoPixel')
    @patch('app.board.neopixels.Pin')
    def test_neopixels_write(self, mock_pin_class, mock_neopixel_class):
        from app.board.neopixels import NeoPixels
        
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_row1 = Mock()
        mock_row2 = Mock()
        mock_row3 = Mock()
        mock_row4 = Mock()
        mock_neopixel_class.side_effect = [mock_row1, mock_row2, mock_row3, mock_row4]
        
        pixels = NeoPixels()
        pixels.write()
        
        mock_row1.write.assert_called_once()
        mock_row2.write.assert_called_once()
        mock_row3.write.assert_called_once()
        mock_row4.write.assert_called_once()

    @patch('app.board.neopixels.NeoPixel')
    @patch('app.board.neopixels.Pin')
    def test_neopixels_pixel_coords_method_exists(self, mock_pin_class, mock_neopixel_class):
        from app.board.neopixels import NeoPixels
        
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_neopixel = Mock()
        mock_neopixel_class.return_value = mock_neopixel
        
        pixels = NeoPixels()
        
        self.assertTrue(hasattr(pixels, 'pixel_coords'))
        self.assertTrue(callable(getattr(pixels, 'pixel_coords', None)))


if __name__ == '__main__':
    unittest.main()