import json
import os

class ConfigLoader:
    @staticmethod
    def load_config(env='server'):
        config_path = f'./{env}/config.json'
        with open(config_path) as f:
            config = json.load(f)
        return config