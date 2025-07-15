import json
import machine
import binascii

class Config:

    filename = 'config.json'
    versionfile = 'app/.version'

    @staticmethod
    def device_uuid():
        return binascii.hexlify(machine.unique_id()).upper()
    
    def __init__(self):
        self._raw = {}
        self._version = 'v0.0.0'

    def load(self):
        # Load the config file
        try:
            with open(Config.filename, 'r') as file:
                self.raw = json.load(file)
        except Exception as e:
            if self.raw is not None:
                raise e
            else:
                self.raw = {}

        # Load the version file
        try:
            with open(Config.versionfile, 'r') as f:
                self._version = f.read().replace('[\n\r\t ]', '')
        except Exception as e:
            if self._version is not None:
                raise e
            else:
                self._version = 'v0.0.0'

    def dump(self):
        with open(Config.filename, 'w') as f:
            json.dump(self._raw, f)

    def publicinfo(self) -> str:
        safe_value = self._raw.copy()
        del safe_value["wifi"]

        return json.dumps({
            "_uuid": Config.device_uuid(),
            "_version": self._version,
            "config": safe_value,
        })
