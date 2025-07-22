import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestBoardBoard(unittest.TestCase):

    def test_board_init(self):
        from app.board.board import Board
        
        board = Board(flipped=True)
        
        self.assertTrue(board.flipped)
        self.assertFalse(board.accepting_inputs)
        self.assertFalse(board.preparing_update)
        self.assertFalse(board.preparing_pairing)
        self.assertEqual(board._pressed, {})
        self.assertFalse(board._should_update)
        self.assertFalse(board._should_pair)

    def test_board_constants(self):
        from app.board.board import Board
        
        self.assertEqual(Board.update_longpress_ms, 5000)
        self.assertEqual(Board.pairing_longpress_ms, 5000)

    @patch('app.board.board.RgbLED')
    @patch('app.board.board.PushButton')
    def test_basic_button_board_init(self, mock_button_class, mock_led_class):
        from app.board.board import BasicButtonBoard
        
        mock_led = Mock()
        mock_button = Mock()
        buttons = {"button1": mock_button}
        
        board = BasicButtonBoard(led=mock_led, buttons=buttons)
        
        self.assertEqual(board.led, mock_led)
        self.assertEqual(board.buttons, buttons)
        self.assertIsNotNone(board.on_press)
        self.assertIsNotNone(board.on_wifi_connecting)
        self.assertIsNotNone(board.on_wifi_connected)
        self.assertIsNotNone(board.on_wifi_failed)

    @patch('app.board.board.RgbLED')
    @patch('app.board.board.PushButton')
    def test_basic_button_board_enable_disable(self, mock_button_class, mock_led_class):
        from app.board.board import BasicButtonBoard
        
        mock_led = Mock()
        mock_button = Mock()
        buttons = {"button1": mock_button}
        
        board = BasicButtonBoard(led=mock_led, buttons=buttons)
        
        board.enable()
        self.assertTrue(board.accepting_inputs)
        
        board.disable()
        self.assertFalse(board.accepting_inputs)

    @patch('app.board.board.RgbLED')
    @patch('app.board.board.Wheel')
    def test_dial_board_init(self, mock_wheel_class, mock_led_class):
        from app.board.board import DialBoard
        
        mock_led = Mock()
        mock_wheel = Mock()
        buttons = {}
        wheel_routines = []
        
        board = DialBoard(
            led=mock_led,
            buttons=buttons,
            dial=mock_wheel,
            wheel_routines=wheel_routines
        )
        
        self.assertEqual(board.led, mock_led)
        self.assertEqual(board.buttons, buttons)
        self.assertEqual(board.dial, mock_wheel)
        self.assertEqual(board.wheel_routines, wheel_routines)
        self.assertIsNotNone(board.on_dial_press)
        self.assertIsNotNone(board.on_dial_longpress)

    @patch('app.board.board.RgbLED')
    @patch('app.board.board.Wheel')
    def test_dial_board_enable_disable(self, mock_wheel_class, mock_led_class):
        from app.board.board import DialBoard
        
        mock_led = Mock()
        mock_wheel = Mock()
        buttons = {}
        
        board = DialBoard(
            led=mock_led,
            buttons=buttons,
            dial=mock_wheel,
            wheel_routines=[]
        )
        
        board.enable()
        self.assertTrue(board.accepting_inputs)
        
        board.disable()
        self.assertFalse(board.accepting_inputs)


if __name__ == '__main__':
    unittest.main()