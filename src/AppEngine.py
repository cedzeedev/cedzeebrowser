import os
import sys
import csv
import traceback
import requests

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup

from src.fBridge import CedzeeBridge
from src.ConsoleLogger import logger
from src.CustomWebEnginePage import CustomWebEnginePage, directory, mapping_urls

from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import (
    Qt,
    QUrl,
    QObject,
    pyqtSlot,
    QThread,
    pyqtSignal,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineDownloadRequest,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QFileDialog,
)

# Set Chromium flags for better performance
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
Window_width = 1200
Window_height = 800
Window_Title = "CEDZEE Browser"

CONFIG_FILE = os.path.abspath(f"{directory}/resources/config.json")


class Worker(QObject):
    """
    Generic worker for running functions in a QThread.
    """

    finished = pyqtSignal()
    result = pyqtSignal(object)
    error = pyqtSignal(tuple)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        try:
            output = self.fn(*self.args, **self.kwargs)
            self.result.emit(output)
        except Exception as e:
            self.error.emit((e, traceback.format_exc()))
        finally:
            self.finished.emit()


class NetworkRequestLogger(QWebEngineUrlRequestInterceptor):
    """
    Logs network requests (currently does nothing).
    """

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        method = info.requestMethod().data().decode("utf-8")
        resource_type = info.resourceType()
        # Could log or process requests here


class BrowserWindow(QMainWindow):
    """
    Main browser window for Cedzee Browser.
    """

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
                os.path.abspath(f"{directory}/theme/browser.css"), "r", encoding="utf-8"
            ) as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.error("browser.css not found.")

        self.browser = QWebEngineView()
        page = CustomWebEnginePage(
            self.profile, self.browser, browser_window=self, open_as="app"
        )
        self.browser.setPage(page)

        self._attach_webchannel(self.browser)

        self.browser.titleChanged.connect(self.update_window_title)
        self.browser.loadFinished.connect(self.handle_load_finished)

        self.main_layout.addWidget(self.browser)

        self.load_history()
        self.thread_pool = {}

    def _attach_webchannel(self, browser: QWebEngineView):
        channel = QWebChannel(self)
        bridge = CedzeeBridge(self)
        bridge.set_web_profile(self.profile)
        bridge.set_web_page(browser.page())
        channel.registerObject("cedzeebrowser", bridge)
        browser.page().setWebChannel(channel)
        bridge.settingChanged.connect(
            lambda k, v: logger.info(f"Setting '{k}' updated on '{v}'")
        )

    def go_home(self):
        self.browser.setUrl(QUrl(mapping_urls["home"]))

    @staticmethod
    def _is_internet_available_worker() -> bool:
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.RequestException:
            return False

    def handle_load_finished(self, ok: bool):
        # If page failed to load, check internet and show offline page if needed
        if not ok:
            current_url = self.browser.url()
            if not current_url.isLocalFile() and current_url.scheme() in (
                "http",
                "https",
            ):
                self.thread = QThread()
                self.worker = Worker(self._is_internet_available_worker)
                self.worker.moveToThread(self.thread)

                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.worker.result.connect(self._handle_internet_check_result)

                self.thread.start()
        else:
            self.save_to_history(self.browser.url().toString(), self.browser.title())
            self.browser.page().inject_extensions(self.browser.url())

    def _handle_internet_check_result(self, is_available):
        if not is_available:
            logger.info("No Internet connection detected. Displaying offline page.")
            self.browser.setUrl(QUrl.fromLocalFile(mapping_urls.get("offline")))

    def update_window_title(self, title):
        self.setWindowTitle(title)

    def ensure_history_file(self):
        history_dir = os.path.join(directory, "resources", "config")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def _save_to_history_worker(self, url_str: str, title: str):
        history_path = os.path.join(directory, "resources", "config", "history.csv")
        try:
            with open(history_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url_str, title]
                )
        except Exception as e:
            logger.error(f"Error while writing to history : {e}")

    def save_to_history(self, url_str: str, title: str):
        # Only save valid URLs and titles
        if not (
            url_str.startswith("http://")
            or url_str.startswith("https://")
            or url_str.startswith("file:///")
        ):
            return
        if not title or title.startswith("http") or title == "Chargement...":
            return

        thread = QThread()
        worker = Worker(self._save_to_history_worker, url_str, title)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

        self.thread_pool[id(thread)] = (thread, worker)
        thread.finished.connect(lambda: self.thread_pool.pop(id(thread), None))

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
                logger.info(f"Download complete : {path}")

        download_item.stateChanged.connect(done)

    def open_new_tab(self):
        self.browser.setUrl(QUrl.fromLocalFile(mapping_urls["home"]))

    def finalize_initial_load(self, data):
        """
        Finalize window setup after initial load (meta tags, window state, etc).
        """
        if data.get("error"):
            logger.error(data["error"])
            self.browser.setUrl(QUrl.fromLocalFile(mapping_urls.get("offline")))
            return

        local_width = Window_width
        local_height = Window_height
        local_title = Window_Title

        if data.get("width") is not None:
            local_width = data["width"]
        if data.get("height") is not None:
            local_height = data["height"]
        if data.get("title") is not None:
            local_title = data["title"]

        self.resize(local_width, local_height)
        self.setWindowTitle(local_title)

        flags = self.windowFlags()

        if data.get("caption") == "false":
            flags |= Qt.WindowType.FramelessWindowHint

        if data.get("sysmenu") == "false":
            flags &= ~Qt.WindowType.WindowSystemMenuHint
        else:
            if data.get("maximizebutton") == "false":
                flags &= ~Qt.WindowType.WindowMaximizeButtonHint
            elif data.get("maximizebutton") == "true":
                flags |= Qt.WindowType.WindowMaximizeButtonHint

            if data.get("minimizebutton") == "false":
                flags &= ~Qt.WindowType.WindowMinimizeButtonHint
            elif data.get("minimizebutton") == "true":
                flags |= Qt.WindowType.WindowMinimizeButtonHint

        if data.get("showintaskbar") == "false":
            flags |= Qt.WindowType.Tool
        elif data.get("showintaskbar") == "true":
            flags &= ~Qt.WindowType.Tool

        self.setWindowFlags(flags)

        if data["is_local_file"] and data["html_content"]:
            self.browser.setHtml(data["html_content"], QUrl(data["final_url"]))
        else:
            self.browser.setUrl(QUrl(data["final_url"]))

        state = data.get("windowstate", "normal")
        if state == "fullscreen":
            self.showFullScreen()
        elif state == "maximized":
            self.showMaximized()
        elif state == "minimized":
            self.showMinimized()
        else:
            self.show()


def perform_initial_load(url):
    """
    Load initial HTML and meta info from local file or URL.
    """
    data = {
        "html_content": "",
        "final_url": url,
        "width": None,
        "height": None,
        "title": None,
        "is_local_file": url.startswith("file://"),
        "error": None,
        "caption": None,
        "sysmenu": None,
        "maximizebutton": None,
        "minimizebutton": None,
        "showintaskbar": None,
        "windowstate": "normal",
    }

    if data["is_local_file"]:
        parsed = urlparse(url)
        path_from_uri = unquote(parsed.path)
        netloc = unquote(parsed.netloc)

        full_path = ""
        if sys.platform.startswith("win"):
            full_path = netloc + path_from_uri
            if full_path.startswith("/") and len(full_path) > 2 and full_path[2] == ":":
                full_path = full_path[1:]
        else:
            full_path = path_from_uri

        path_obj = Path(full_path)
        if not path_obj.exists():
            data["error"] = f"Fichier introuvable : {path_obj}"
            return data

        with open(path_obj, "r", encoding="utf-8") as f:
            data["html_content"] = f.read()
    else:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data["html_content"] = response.text
        except requests.RequestException as e:
            data["error"] = f"Erreur lors du téléchargement de l'URL {url}: {e}"
            data["final_url"] = QUrl.fromLocalFile(
                mapping_urls.get("offline")
            ).toString()
            return data

    if data["html_content"]:
        soup = BeautifulSoup(data["html_content"], "html.parser")

        meta_map = {
            "width": "cedzeeapp_horizontal",
            "height": "cedzeeapp_vertical",
            "title": "cedzeeapp_title",
            "caption": "cedzeeapp_caption",
            "sysmenu": "cedzeeapp_sysmenu",
            "maximizebutton": "cedzeeapp_maximizebutton",
            "minimizebutton": "cedzeeapp_minimizebutton",
            "showintaskbar": "cedzeeapp_showintaskbar",
            "windowstate": "cedzeeapp_windowstate",
        }

        for key, attr_name in meta_map.items():
            meta_tag = soup.find("meta", attrs={attr_name: True})
            if meta_tag and meta_tag.has_attr(attr_name):
                value = meta_tag[attr_name].lower()
                if key in ["width", "height"]:
                    try:
                        data[key] = int(value)
                    except ValueError:
                        logger.error(f"Invalid value for {attr_name}: {value}")
                else:
                    data[key] = value

    return data


def start_app(url: str):
    """
    Start a new browser window and load the given URL.
    """
    window = BrowserWindow()
    window.browser.setHtml("<h1>Loading...</h1>")
    window.finalize_initial_load(perform_initial_load(url))

    return window


if __name__ == "__main__":
    """Main entry point for the Cedzee Browser application."""
    app = QApplication(sys.argv)

    initial_load_url = mapping_urls["home"]

    if len(sys.argv) > 1:

        arg_path = sys.argv[1]

        if os.path.exists(arg_path):
            initial_load_url = QUrl.fromLocalFile(os.path.abspath(arg_path)).toString()
            logger.info(f"Attempt to load the local file: {initial_load_url}")

        else:
            logger.info(
                f"The argument provided '{arg_path}' is not a valid file path. Loading the default homepage URL."
            )

    main_window = start_app(initial_load_url)
    main_window.show()

    sys.exit(app.exec())
