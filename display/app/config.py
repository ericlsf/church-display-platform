import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.json"


class Config:
    def __init__(self):
        self.data = {}

    def load(self):
        with open(CONFIG_PATH, "r") as f:
            self.data = json.load(f)
        return self.data

    def get(self, key, default=None):
        return self.data.get(key, default)
