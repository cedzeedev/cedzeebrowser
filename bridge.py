import json
import os
import base64
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QVariant
try:
    import requests
except ImportError:
    print("error: requests library not installed. Please install it using 'pip install requests'.")
    requests = None

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

    @pyqtSlot(str, "QVariantMap", result="QVariantMap")
    def fetchUrl(self, url: str, init: dict) -> dict:
        method = init.get('method', 'GET').upper()
        headers = init.get('headers', {}) or {}
        body = init.get('body', None)
        timeout = init.get('timeout', 10)

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=body,
                timeout=timeout,
                stream=True
            )
            status = response.status_code
            status_text = response.reason
            resp_headers = dict(response.headers)

            content_type = response.headers.get('Content-Type', '')
            # Gestion des images : renvoyer en base64
            if content_type.startswith('image/'):
                data = response.content
                b64 = base64.b64encode(data).decode('utf-8')
                data_url = f"data:{content_type};base64,{b64}"
                resp_body = data_url
            elif 'application/json' in content_type:
                try:
                    resp_body = response.json()
                except ValueError:
                    resp_body = response.text
            else:
                resp_body = response.text

            return {
                'status': status,
                'statusText': status_text,
                'headers': resp_headers,
                'body': resp_body
            }
        except requests.exceptions.RequestException as e:
            err = str(e)
            code = None
            if hasattr(e, 'response') and e.response is not None:
                code = e.response.status_code
            return {
                'error': err,
                'status': code
            }

    @pyqtSlot(result='QVariantMap')
    def getAll(self) -> dict:
        return self._config
