import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.config.config import Config, ConfigValue


class TestConfigValue(unittest.TestCase):

    def test_get_wifi_with_complete_config(self):
        config_value = ConfigValue(
            {'wifi': {
                'ssid': 'test_network',
                'pass': 'test_password'
            }})

        ssid, password, success = config_value.get_wifi()

        self.assertEqual(ssid, 'test_network')
        self.assertEqual(password, 'test_password')
        self.assertTrue(success)

    def test_get_wifi_missing_wifi_section(self):
        config_value = ConfigValue({})

        ssid, password, success = config_value.get_wifi()

        self.assertEqual(ssid, "")
        self.assertEqual(password, "")
        self.assertFalse(success)

    def test_get_wifi_missing_ssid(self):
        config_value = ConfigValue({'wifi': {'pass': 'test_password'}})

        ssid, password, success = config_value.get_wifi()

        self.assertEqual(ssid, "")
        self.assertEqual(password, "")
        self.assertFalse(success)

    def test_get_wifi_missing_pass(self):
        config_value = ConfigValue({'wifi': {'ssid': 'test_network'}})

        ssid, password, success = config_value.get_wifi()

        self.assertEqual(ssid, "")
        self.assertEqual(password, "")
        self.assertFalse(success)


class TestConfig(unittest.TestCase):

    def test_config_init(self):
        config = Config()

        self.assertIsInstance(config.value, ConfigValue)
        self.assertEqual(config.version, 'v0.0.0')

    @patch('app.config.config.machine.unique_id')
    @patch('app.config.config.binascii.hexlify')
    def test_device_uuid(self, mock_hexlify, mock_unique_id):
        mock_unique_id.return_value = b'test_id'
        mock_hexlify.return_value = b'TEST_ID_HEX'

        result = Config.device_uuid()

        mock_unique_id.assert_called_once()
        mock_hexlify.assert_called_once_with(b'test_id')
        self.assertEqual(result, b'TEST_ID_HEX')

    @patch('builtins.open',
           new_callable=mock_open,
           read_data='{"name": "test_device"}')
    def test_load_config_success(self, mock_file):
        config = Config()

        config.load()

        mock_file.assert_called()
        self.assertIsInstance(config.raw, ConfigValue)

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_config_file_not_found(self, mock_file):
        config = Config()
        config.raw = None

        config.load()

        self.assertIsInstance(config.raw, ConfigValue)
        self.assertEqual(config.raw, {})

    @patch('builtins.open')
    def test_load_config_json_error(self, mock_file):
        mock_file.side_effect = [
            mock_open(read_data='invalid json').return_value,
            mock_open(read_data='v1.0.0').return_value
        ]

        config = Config()
        config.raw = ConfigValue({'existing': 'data'})

        with self.assertRaises(Exception):
            config.load()

    @patch('builtins.open')
    def test_load_version_success(self, mock_file):
        mock_file.side_effect = [
            mock_open(read_data='{"name": "test"}').return_value,
            mock_open(read_data='v2.1.0').return_value
        ]

        config = Config()

        config.load()

        self.assertEqual(config.version, 'v2.1.0')

    @patch('builtins.open')
    def test_load_version_file_not_found(self, mock_file):
        mock_file.side_effect = [
            mock_open(read_data='{"name": "test"}').return_value,
            FileNotFoundError()
        ]

        config = Config()
        original_version = config.version

        config.load()

        self.assertEqual(config.version, original_version)

    def test_config_constants(self):
        self.assertEqual(Config.filename, 'config.json')
        self.assertEqual(Config.versionfile, 'app/.version')


if __name__ == '__main__':
    unittest.main()
