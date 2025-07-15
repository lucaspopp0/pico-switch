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

    filename = 'config.json'
    versionfile = 'app/.version'
    
    def __init__(self):
        self.value = ConfigValue({})
        self.version = 'v0.0.0'

    def load(self):
        # Load the config file
        try:
            with open(Config.filename, 'r') as file:
                self.raw = ConfigValue(json.load(file))
        except Exception as e:
            if self.raw is not None:
                raise e
            else:
                self.raw = ConfigValue({})

        # Load the version file
        try:
            with open(Config.versionfile, 'r') as f:
                self.version = f.read().replace('[\n\r\t ]', '')
        except Exception as e:
            if self.version is not None:
                raise e
            else:
                self.version = 'v0.0.0'

    def dump(self):
        with open(Config.filename, 'w') as f:
            json.dump(self.raw, f)

    def publicinfo(self) -> str:
        safe_value = self.raw.copy()
        del safe_value["wifi"]

        return json.dumps({
            "_uuid": Config.device_uuid(),
            "_version": self.version,
            "config": safe_value,
        })
