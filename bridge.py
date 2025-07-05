import json
import os
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "resources", "config.json")

class CedzeeBridge(QObject):
    settingChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_config()

    def _load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {}

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4)

    @pyqtSlot(str, str)
    def set(self, key: str, value: str):
        self._config[key] = value
        self._save_config()
        self.settingChanged.emit(key, value)

    @pyqtSlot(str, result=str)
    def get(self, key: str) -> str:
        return self._config.get(key, "")

    @pyqtSlot(result='QVariantMap')
    def getAll(self):
        return self._config
