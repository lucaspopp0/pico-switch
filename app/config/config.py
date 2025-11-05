import json
import machine
import binascii


class ConfigValue(dict):

    # Return the wifi configuration, if it exists
    def get_wifi(self) -> tuple[str, str, bool]:
        if 'wifi' in self:
            if 'ssid' in self['wifi'] and 'pass' in self['wifi']:
                return (
                    self['wifi']['ssid'],
                    self['wifi']['pass'],
                    True,
                )

        return ("", "", False)


class Config:

    @staticmethod
    def device_uuid():
        return binascii.hexlify(machine.unique_id()).upper()

    filename = '../../config.json'
    versionfile = '../app/.version'

    def __init__(self):
        self.value = ConfigValue({})
        self.version = 'v0.0.0'

    def load(self):
        # Load the config file
        with open(Config.filename, 'r') as file:
            self.value = ConfigValue(json.load(file))

        # Load the version file
        try:
            with open(Config.versionfile, 'r') as f:
                self.version = f.read().replace('[\n\r\t ]', '')
        except Exception as e:
            print("Failed to load version:" + str(e))

    def dump(self):
        with open(Config.filename, 'w') as f:
            json.dump(self.value, f)

    def publicinfo(self) -> str:
        safe_value = self.value.copy()
        del safe_value["wifi"]

        return json.dumps({
            "_uuid": Config.device_uuid(),
            "_version": self.version,
            "config": safe_value,
        })
