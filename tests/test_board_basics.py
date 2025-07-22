import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestBoardBasics(unittest.TestCase):

    @patch('app.board.basics.Pin')
    def test_push_button_init(self, mock_pin_class):
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        from app.board import basics
        
        button = basics.PushButton([1, 2], "test_key")
        
        self.assertEqual(button.pins, [1, 2])
        self.assertEqual(button.key, "test_key")
        self.assertEqual(len(button.gpios), 2)
        self.assertFalse(button.last_pressed)
        self.assertFalse(button.pressed)
        
        self.assertEqual(mock_pin_class.call_count, 2)
        mock_pin.irq.assert_called()

    @patch('app.board.basics.Pin')
    @patch('app.board.basics.Timer')
    def test_push_button_on_change_pressed(self, mock_timer_class, mock_pin_class):
        mock_pin = Mock()
        mock_pin.value.return_value = 0
        mock_pin_class.return_value = mock_pin
        
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer
        
        from app.board import basics
        
        button = basics.PushButton([1], "test")
        
        mock_on_press = Mock()
        button.on_press = mock_on_press
        
        button.pressed = True
        button.last_pressed = False
        
        with patch('builtins.print'):
            button._on_change()
        
        mock_on_press.assert_called_once_with("test")
        mock_timer_class.assert_called_once()

    @patch('app.board.basics.Pin')
    def test_push_button_on_change_released(self, mock_pin_class):
        mock_pin = Mock()
        mock_pin.value.return_value = 1
        mock_pin_class.return_value = mock_pin
        
        from app.board import basics
        
        button = basics.PushButton([1], "test")
        
        mock_on_release = Mock()
        button.on_release = mock_on_release
        
        mock_timer = Mock()
        button.long_press_timer = mock_timer
        
        button.pressed = False
        button.last_pressed = True
        
        button._on_change()
        
        mock_on_release.assert_called_once_with("test")
        mock_timer.deinit.assert_called_once()

    @patch('app.board.basics.Pin')
    def test_push_button_on_interrupt(self, mock_pin_class):
        mock_pin = Mock()
        mock_pin.value.return_value = 0
        mock_pin_class.return_value = mock_pin
        
        from app.board import basics
        
        button = basics.PushButton([1], "test")
        
        with patch.object(button, '_on_change') as mock_on_change:
            button._on_interrupt()
        
        mock_on_change.assert_called_once()

    @patch('app.board.basics.Pin')
    @patch('app.board.basics.PWM')
    def test_rgb_led_init(self, mock_pwm_class, mock_pin_class):
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_pwm = Mock()
        mock_pwm_class.return_value = mock_pwm
        
        from app.board import basics
        
        led = basics.RgbLED(16, 17, 18)
        
        self.assertEqual(mock_pin_class.call_count, 3)
        self.assertEqual(mock_pwm_class.call_count, 3)
        mock_pwm.freq.assert_called_with(1_000)

    @patch('app.board.basics.Pin')
    @patch('app.board.basics.PWM')
    def test_rgb_led_off(self, mock_pwm_class, mock_pin_class):
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_pwm = Mock()
        mock_pwm_class.return_value = mock_pwm
        
        from app.board import basics
        
        led = basics.RgbLED(16, 17, 18)
        led.off()
        
        self.assertEqual(mock_pwm.duty_u16.call_count, 3)
        mock_pwm.duty_u16.assert_called_with(0)

    @patch('app.board.basics.Pin')
    @patch('app.board.basics.PWM')
    def test_rgb_led_do_color(self, mock_pwm_class, mock_pin_class):
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_pwm_r = Mock()
        mock_pwm_g = Mock()
        mock_pwm_b = Mock()
        
        mock_pwm_class.side_effect = [mock_pwm_r, mock_pwm_g, mock_pwm_b]
        
        from app.board import basics
        
        led = basics.RgbLED(16, 17, 18)
        led.do_color(50, 75, 100)
        
        expected_r = basics.RgbLED.pwmFreq(50)
        expected_g = basics.RgbLED.pwmFreq(75)
        expected_b = basics.RgbLED.pwmFreq(100)
        
        mock_pwm_r.duty_u16.assert_called_with(expected_r)
        mock_pwm_g.duty_u16.assert_called_with(expected_g)
        mock_pwm_b.duty_u16.assert_called_with(expected_b)

    def test_rgb_led_pwm_freq(self):
        from app.board import basics
        
        result = basics.RgbLED.pwmFreq(50)
        expected = int((50 / 100.0) * 65_535.0)
        
        self.assertEqual(result, expected)

    @patch('app.board.basics.Pin')
    @patch('app.board.basics.PWM')
    @patch('app.board.basics.time.sleep')
    async def test_rgb_led_flash(self, mock_sleep, mock_pwm_class, mock_pin_class):
        mock_pin = Mock()
        mock_pin_class.return_value = mock_pin
        
        mock_pwm = Mock()
        mock_pwm_class.return_value = mock_pwm
        
        from app.board import basics
        
        led = basics.RgbLED(16, 17, 18)
        
        with patch.object(led, 'do_color') as mock_do_color:
            with patch.object(led, 'off') as mock_off:
                await led.flash(100, 50, 25, seconds=0.2, times=2)
        
        self.assertEqual(mock_do_color.call_count, 2)
        self.assertEqual(mock_off.call_count, 2)
        mock_do_color.assert_called_with(100, 50, 25)
        mock_sleep.assert_called_with(0.2)


if __name__ == '__main__':
    unittest.main()