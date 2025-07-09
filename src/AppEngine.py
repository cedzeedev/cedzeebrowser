import os
import sys
import csv
import json
from datetime import datetime
import requests
from pathlib import Path

from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from src.bridge import CedzeeBridge
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
    QWebEngineUrlRequestInfo,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QToolBar,
    QWidget,
    QHBoxLayout,
    QFileDialog,
    QSizePolicy,
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

application = QApplication.instance()
directory1 = os.path.dirname(os.path.abspath(__file__))
directory = os.path.dirname(directory1)

if not application:
    application = QApplication(sys.argv)

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
        method = info.requestMethod().data().decode("utf-8")
        resource_type = info.resourceType()


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None, browser_window=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window

    def createWindow(self, _type):
        if self.browser_window and self.browser_window.browser:
            return self.browser_window.browser.page()
        return super().createWindow(_type)

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
                print(
                    f"Unknown cedzee:// path: {url.toString()}. Loading home.",
                    file=sys.stderr,
                )
                self.setUrl(QUrl.fromLocalFile(home_url))
            return False
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)

    def certificateError(self, certificate_error: QWebEngineCertificateError):
        print(
            f"Erreur de certificat détectée pour {certificate_error.url().toString()}: {certificate_error.errorDescription()}",
            file=sys.stderr,
        )
        return True


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ensure_history_file()

        self.setWindowTitle(Window_Title)
        self.resize(Window_width, Window_height)
        self.move(300, 50)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

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
            with open(
                os.path.abspath(f"{directory}/theme/theme.css"), "r", encoding="utf-8"
            ) as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("theme.css not found.")

        self.browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, self.browser, browser_window=self)
        self.browser.setPage(page)

        self._attach_webchannel(self.browser)

        self.browser.titleChanged.connect(self.update_window_title)
        self.browser.loadFinished.connect(self.handle_load_finished)

        self.main_layout.addWidget(self.browser)

        # self.menu = QToolBar("Menu de navigation")
        # self.addToolBar(self.menu)
        # self.add_navigation_buttons()

        self.load_history()

    def _attach_webchannel(self, browser: QWebEngineView):
        channel = QWebChannel(self)
        bridge = CedzeeBridge(self)
        channel.registerObject("cedzeebrowser", bridge)
        browser.page().setWebChannel(channel)
        bridge.settingChanged.connect(
            lambda k, v: print(f"Setting '{k}' mis à jour en '{v}'")
        )

    # def add_navigation_buttons(self):
    #     icons = {
    #         "back": "arrow_back.png",
    #         "forward": "arrow_forward.png",
    #         "refresh": "refresh.png",
    #         "home": "home.png",
    #     }

    #     for name, fn in [
    #         ("home", self.go_home),
    #         ("refresh", lambda: self.browser.reload()),
    #     ]:
    #         btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
    #         btn.setToolTip(name.capitalize())
    #         btn.triggered.connect(fn)
    #         self.menu.addAction(btn)

    #     spacer = QWidget()
    #     spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    #     self.menu.addWidget(spacer)

    #     for name, fn in [
    #         ("back", lambda: self.browser.back()),
    #         ("forward", lambda: self.browser.forward()),
    #     ]:
    #         btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
    #         btn.setToolTip(name.capitalize())
    #         btn.triggered.connect(fn)
    #         self.menu.addAction(btn)

    def go_home(self):
        self.browser.setUrl(QUrl(home_url))

    @staticmethod
    def is_internet_available() -> bool:
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False

    def handle_load_finished(self, ok: bool):
        if not ok:
            current_url = self.browser.url()
            if not current_url.isLocalFile() and current_url.scheme() in (
                "http",
                "https",
            ):
                if not BrowserWindow.is_internet_available():
                    print(
                        "Pas de connexion Internet détectée. Affichage page offline.",
                        file=sys.stderr,
                    )
                    self.browser.setUrl(QUrl.fromLocalFile(offline_url))
        else:
            self.save_to_history(self.browser.url().toString(), self.browser.title())

    def update_window_title(self, title):
        self.setWindowTitle(title)

    def ensure_history_file(self):
        history_dir = os.path.join(directory, "resources", "config")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def save_to_history(self, url_str: str, title: str):
        if (
            url_str.startswith("http://")
            or url_str.startswith("https://")
            or url_str.startswith("file:///")
        ):
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


def start_app(url: str):
    global home_url
    global Window_width
    global Window_height
    global Window_Title

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    html_content = ""
    is_local_file = url.startswith("file://")

    if is_local_file:
        parsed = urlparse(url)
        path = unquote(parsed.path)

        if sys.platform.startswith("win"):
            if path.startswith("/") and len(path) > 2 and path[2] == ":":
                path = path[1:]

        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Fichier introuvable : {path_obj}")

        with open(path_obj, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        try:
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
        except requests.RequestException as e:
            print(f"Erreur lors du téléchargement de l'URL {url}: {e}", file=sys.stderr)
            url = QUrl.fromLocalFile(offline_url).toString()
            html_content = ""

    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        horizontal = soup.find("meta", attrs={"cedzeeapp_horizontal": True})
        vertical = soup.find("meta", attrs={"cedzeeapp_vertical": True})
        title = soup.find("meta", attrs={"cedzeeapp_title": True})

        if horizontal:
            try:
                Window_width = int(horizontal["cedzeeapp_horizontal"])
            except ValueError:
                print(
                    f"Invalid cedzeeapp_horizontal value: {horizontal['cedzeeapp_horizontal']}"
                )

        if vertical:
            try:
                Window_height = int(vertical["cedzeeapp_vertical"])
            except ValueError:
                print(
                    f"Invalid cedzeeapp_vertical value: {vertical['cedzeeapp_vertical']}"
                )

        if title:
            Window_Title = title["cedzeeapp_title"]

    home_url = url

    window = BrowserWindow()
    if is_local_file and html_content:
        window.browser.setHtml(html_content, QUrl(url))
    else:
        window.browser.setUrl(QUrl(url))

    window.show()

    if not QApplication.instance().startingUp():
        app.exec()


if __name__ == "__main__":
    initial_load_url = home_url
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            initial_load_url = QUrl.fromLocalFile(os.path.abspath(arg_path)).toString()
            print(f"Tentative de chargement du fichier local: {initial_load_url}")
        else:
            print(
                f"L'argument fourni '{arg_path}' n'est pas un chemin de fichier valide. Chargement de l'URL d'accueil par défaut."
            )

    start_app(initial_load_url)
