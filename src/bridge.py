import json
import os
import base64
import shutil
from src.Update import update_all
from functools import wraps
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QVariant
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineCore import QWebEnginePage


try:
    import requests
except ImportError:
    print(
        "error: requests library not installed. Please install it using 'pip install requests'."
    )
    requests = None

directory1 = os.path.dirname(os.path.abspath(__file__))
directory = os.path.dirname(directory1)
CONFIG_FILE = f"{directory}/resources/config.json"


def require_local_url(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.web_page:
            print("⚠️ web_page non défini.")
            return None
        url = self.web_page.url().toString()
        if not url.startswith("file:///"):
            return None
        return method(self, *args, **kwargs)

    return wrapper


class CedzeeBridge(QObject):
    settingChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_config()
        self.web_profile = None
        self.web_page = None

    def _load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {}

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4)

    def set_web_profile(self, profile: QWebEngineProfile):
        self.web_profile = profile

    def set_web_page(self, page: QWebEnginePage):
        self.web_page = page

    @pyqtSlot(str, str)
    @require_local_url
    def set(self, key: str, value: str):
        self._config[key] = value
        self._save_config()
        self.settingChanged.emit(key, value)

    @pyqtSlot(str, result=str)
    @require_local_url
    def get(self, key: str) -> str:
        return self._config.get(key, "")

    @pyqtSlot(str, "QVariantMap", result="QVariantMap")
    @require_local_url
    def fetchUrl(self, url: str, init: dict) -> dict:
        method = init.get("method", "GET").upper()
        headers = init.get("headers", {}) or {}
        body = init.get("body", None)
        timeout = init.get("timeout", 10)

        try:
            response = requests.request(
                method, url, headers=headers, data=body, timeout=timeout, stream=True
            )
            status = response.status_code
            status_text = response.reason
            resp_headers = dict(response.headers)

            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("image/"):
                data = response.content
                b64 = base64.b64encode(data).decode("utf-8")
                data_url = f"data:{content_type};base64,{b64}"
                resp_body = data_url
            elif "application/json" in content_type:
                try:
                    resp_body = response.json()
                except ValueError:
                    resp_body = response.text
            else:
                resp_body = response.text

            return {
                "status": status,
                "statusText": status_text,
                "headers": resp_headers,
                "body": resp_body,
            }
        except requests.exceptions.RequestException as e:
            err = str(e)
            code = None
            if hasattr(e, "response") and e.response is not None:
                code = e.response.status_code
            return {"error": err, "status": code}

    @pyqtSlot()
    @require_local_url
    def update(self):
        try:
            update_all()
            print("✅ update_all() lancée avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour : {e}")

    @pyqtSlot(result=str)
    @require_local_url
    def get_mode(self) -> str:
        if directory.endswith("_internal"):
            return "app"
        else:
            return "py"

    @pyqtSlot(result="QVariantMap")
    @require_local_url
    def getAll(self) -> dict:
        return self._config

    @pyqtSlot()
    @require_local_url
    def clearCache(self):
        if self.web_profile:
            self.web_profile.clearHttpCache()

    @pyqtSlot()
    @require_local_url
    def clearCookies(self):
        if self.web_profile:
            self.web_profile.cookieStore().deleteAllCookies()

    @pyqtSlot()
    @require_local_url
    def ClearAll(self):
        if self.web_profile:
            self.web_profile.clearHttpCache
            self.web_profile.cookieStore().deleteAllCookies

            if os.path.exists(f"{directory}/resources/saves"):
                if os.path.exists(f"{directory}/resources/config"):
                    if os.path.exists(f"{directory}/resources/saves"):

                        shutil.rmtree(f"{directory}/resources/saves")
                        shutil.rmtree(f"{directory}/resources/config")
                        shutil.rmtree(f"{directory}/resources/saves")
            print("Données supprimés avec succès")

    @pyqtSlot(result=str)
    @require_local_url
    def VerifyUpdate(self) -> str:
        version_json_url = "https://raw.githubusercontent.com/cedzeedev/cedzeebrowser/refs/heads/main/version.json"
        version_file_pth = f"{directory}/version.json"
        try:
            with open(version_file_pth, "r", encoding="utf-8") as file:
                data = json.load(file)
            version = data[0].get("version", "inconnue")
        except Exception as e:
            print(f"Erreur lors du chargement de la version : {e}")
            version = "inconnue"

        def get_online_version():
            try:
                response = requests.get(version_json_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                return data[0].get("version", "inconnue")
            except Exception:
                return "error"

        version_online = get_online_version()
        update_available = False
        if (
            version_online != "error"
            and version != version_online
            and version < version_online
        ):
            update_available = True
            try:
                response = requests.get(version_json_url, timeout=10)
                if response.status_code == 200:
                    with open(
                        f"{directory}/version_online.json", "w", encoding="utf-8"
                    ) as f:
                        f.write(response.text)
            except Exception:
                pass

        if update_available == True:
            return "yes"
        else:
            return "no"

    @pyqtSlot(result=str)
    @require_local_url
    def get_version(self) -> str:
        version_file_pth = f"{directory}/version.json"
        try:
            with open(version_file_pth, "r", encoding="utf-8") as file:
                data = json.load(file)
            version = data[0].get("version", "inconnue")
        except Exception as e:
            print(f"Erreur lors du chargement de la version : {e}")
            version = "inconnue"
        return version
