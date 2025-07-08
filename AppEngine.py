import os
import sys
import csv
import sys
import json
from datetime import datetime
import requests
from pathlib import Path

from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from bridge import CedzeeBridge # Assuming bridge.py exists and CedzeeBridge is defined there
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QObject, pyqtSlot
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineDownloadRequest,
    QWebEngineCertificateError,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo
)
from PyQt6.QtWidgets import (
    QApplication,
    # QLineEdit, # Removed QLineEdit
    QMainWindow,
    QMenu,
    QToolBar,
    QWidget,
    QHBoxLayout,
    QFileDialog,
    QSizePolicy
)

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu "
    "--enable-webgl "
    "--enable-accelerated-2d-canvas "
    "--ignore-gpu-blocklist "
    "--enable-zero-copy "
    "--disable-software-rasterizer "
    "--use-gl=angle "
    "--enable-native-gpu-memory-buffers"
)

# PyQt application setup
application = QApplication.instance()
directory = os.path.dirname(os.path.abspath(__file__))

if not application:
    application = QApplication(sys.argv)

# utils variables
home_url = "https://www.youtube.com"
offline_url = os.path.abspath(f"{directory}/offline/index.html")
history_page_url = os.path.abspath(f"{directory}/web/history.html")
update_page_url = os.path.abspath(f"{directory}/web/update.html")
game_url = os.path.abspath(f"{directory}/offline/game.html")
welcome_url = os.path.abspath(f"{directory}/web/welcome.html")
contributors_url = os.path.abspath(f"{directory}/web/contributors.html")
favorites_url = os.path.abspath(f"{directory}/web/favorites.html")

Window_width = 1200
Window_height = 800
Window_Title = "Cedzee Browser"

CONFIG_FILE = os.path.abspath(f"{directory}/resources/config.json")


class NetworkRequestLogger(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        method = info.requestMethod().data().decode('utf-8')
        resource_type = info.resourceType()
        # print(f"[Network] {method} {url} (Type: {resource_type.name})") # Uncomment to see network requests

# web browser
class CustomWebEnginePage(QWebEnginePage):
    """
    Handles TLS/SSL certificate errors and custom protocol schemes.
    """

    def __init__(self, profile, parent=None, browser_window=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window

    def createWindow(self, _type):
        if self.browser_window and self.browser_window.browser:
            return self


    def acceptNavigationRequest(self, url: QUrl, nav_type, isMainFrame):
        if url.scheme() == "cedzee":
            target = url.toString().replace("cedzee://", "")
            mapping = {
                "home": home_url,
                "history": history_page_url,
                "update": update_page_url,
                "offline": offline_url,
                "game": game_url,
                "welcome": welcome_url,
                "contributors": contributors_url,
                "favorites": favorites_url,
            }
            real_path = mapping.get(target)
            if real_path:
                self.setUrl(QUrl.fromLocalFile(real_path))
            else:
                print(f"Unknown cedzee:// path: {url.toString()}. Loading home.", file=sys.stderr)
                self.setUrl(QUrl.fromLocalFile(home_url))
            return False 
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)

    def certificateError(self, certificate_error: QWebEngineCertificateError):
        print(f"Erreur de certificat détectée pour {certificate_error.url().toString()}: {certificate_error.errorDescription()}", file=sys.stderr)
        return True


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ensure_history_file()

        # Window properties
        self.setWindowTitle(Window_Title)
        self.resize(Window_width, Window_height)
        self.move(300, 50)

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # WebEngine profile setup
        profile_path = f"{directory}/browser_data"
        self.profile = QWebEngineProfile("Default", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(profile_path)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.downloadRequested.connect(self.on_downloadRequested)

        self.request_logger = NetworkRequestLogger()
        self.profile.setUrlRequestInterceptor(self.request_logger)
        try:
            with open(os.path.abspath(f"{directory}/theme/theme.css"), "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("theme.css not found.")

        # Browser view
        self.browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, self.browser, browser_window=self)
        self.browser.setPage(page)
        self.browser.setUrl(QUrl(home_url))
        if Window_Title == "Cedzee Browser":
            self.browser.titleChanged.connect(self.update_window_title)
        self.browser.loadFinished.connect(self.handle_load_finished)
        self.browser.page().javaScriptConsoleMessage = self.handle_js_error
        self.main_layout.addWidget(self.browser)

        # Menu toolbar
        self.menu = QToolBar("Menu de navigation")
        self.addToolBar(self.menu)
        self.add_navigation_buttons()

        self.load_history()

    def _attach_webchannel(self, browser: QWebEngineView):
        channel = QWebChannel(self)
        bridge = CedzeeBridge(self)
        channel.registerObject("cedzeebrowser", bridge)
        browser.page().setWebChannel(channel)
        bridge.settingChanged.connect(
            lambda k, v: print(f"Setting '{k}' mis à jour en '{v}'")
        )

    def add_navigation_buttons(self):
        icons = {
            "back": "arrow_back.png",
            "forward": "arrow_forward.png",
            "refresh": "refresh.png",
            "home": "home.png",
        }

        for name, fn in [
            ("home", self.go_home),
            ("refresh", lambda: self.browser.reload()),
        ]:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.menu.addWidget(spacer)

        # Right icons
        for name, fn in [
            ("back", lambda: self.browser.back()),
            ("forward", lambda: self.browser.forward()),
        ]:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

    def go_home(self):
        self.browser.setUrl(QUrl(home_url))

    def handle_js_error(self, message_level, message, line, sourceID):
        common_errors_to_ignore = [
            "Unrecognized feature: 'ch-ua-form-factors'.",
            "Unrecognized document policy feature name",
            "Deprecated API for given entry type.",
            "An iframe which has both allow-scripts and allow-same-origin",
            "Unrecognized feature: 'attribution-reporting'.",
        ]
        if any(error in message for error in common_errors_to_ignore):
            return

        level_map = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARNING",
            QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
        }
        level_name = level_map.get(message_level, "UNKNOWN_LEVEL")
        print(f"JS Console ({level_name}) : {message} (Ligne: {line}, Source: {sourceID})", file=sys.stderr)

    def handle_load_finished(self, ok: bool):
        if not ok:
            current_url = self.browser.url()
            if not current_url.isLocalFile() and current_url.scheme() in ["http", "https"]:
                print(f"Échec de chargement pour {current_url.toString()}. Redirection vers la page hors ligne.", file=sys.stderr)
                self.browser.setUrl(QUrl.fromLocalFile(offline_url))
        self.save_to_history(self.browser.url().toString(), self.browser.title())

    def update_window_title(self, title):
        self.setWindowTitle(f"CEDZEE Browser - {title}")

    def ensure_history_file(self):
        history_dir = os.path.join(directory, "resources", "config")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def save_to_history(self, url_str: str, title: str):
        if url_str.startswith("http://") or url_str.startswith("https://") or url_str.startswith("file:///"):
            if not title or title.startswith("http") or title == "Chargement...":
                return

            history_path = os.path.join(directory, "resources", "config", "history.csv")
            try:
                with open(history_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url_str, title]
                    )
            except Exception as e:
                print(f"Erreur lors de l'écriture dans l'historique : {e}")

    def load_history(self):
        try:
            with open(
                f"{directory}/resources/config/history.csv", mode="r", encoding="utf-8"
            ) as f:
                reader = csv.reader(f)
                self.history = [row[1] for row in reader if len(row) > 1]
                self.history_index = len(self.history) - 1
        except FileNotFoundError:
            self.history = []
            self.history_index = -1

    def on_downloadRequested(self, download_item: QWebEngineDownloadRequest):
        suggested = download_item.suggestedFileName() or "downloaded_file"
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier", suggested)
        if not path:
            download_item.cancel()
            return
        download_item.setDownloadDirectory(os.path.dirname(path))
        download_item.setDownloadFileName(os.path.basename(path))
        download_item.accept()

        def done(state):
            if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                print(f"Téléchargement terminé : {path}")

        download_item.stateChanged.connect(done)

    def open_new_tab(self):
        self.browser.setUrl(QUrl.fromLocalFile(home_url))


if __name__ == "__main__":
    window = BrowserWindow()
    window.show()
    application.exec()

def start_app(url: str):
    global home_url
    global Window_width
    global Window_height
    global Window_Title


    if url.startswith("file://"):
        parsed = urlparse(url)
        path = unquote(parsed.path)

        if sys.platform.startswith('win'):
            if path.startswith('/') and len(path) > 2 and path[2] == ':':
                path = path[1:]

        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Fichier HTML introuvable : {path_obj}")
        with open(path_obj, 'r', encoding='utf-8') as f:
            html = f.read()
    else:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    horizontal = soup.find('meta', attrs={'cedzeeapp_horizontal': True})
    vertical = soup.find('meta', attrs={'cedzeeapp_vertical': True})
    title = soup.find('meta', attrs={'cedzeeapp_title': True})

    if horizontal:
        Window_width = int(horizontal['cedzeeapp_horizontal'])

    if vertical:
        Window_height = int(vertical['cedzeeapp_vertical'])

    if title:
        Window_Title = title['cedzeeapp_title']

    home_url = url

    window = BrowserWindow()
    window.show()