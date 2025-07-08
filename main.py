import os
import sys
import csv
import json
from datetime import datetime
from AppEngine import start_app 
import requests
from bridge import CedzeeBridge
from Update import update_all
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QObject, pyqtSlot, QRect, QPoint
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
    QLineEdit,
    QMainWindow,
    QMenu,
    QToolBar,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QFrame,
    QPushButton,
    QToolButton
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
directory = os.path.dirname(os.path.abspath(__file__))

if not application:
    application = QApplication(sys.argv)

home_url = os.path.abspath(f"{directory}/web/index.html")
history_page_url = os.path.abspath(f"{directory}/web/history.html")
update_page_url = os.path.abspath(f"{directory}/web/update.html")
offline_url = os.path.abspath(f"{directory}/offline/index.html")
game_url = os.path.abspath(f"{directory}/offline/game.html")
welcome_url = os.path.abspath(f"{directory}/web/welcome.html")
contributors_url = os.path.abspath(f"{directory}/web/contributors.html")
favorites_url = os.path.abspath(f"{directory}/web/favorites.html")
CONFIG_FILE = os.path.abspath(f"{directory}/resources/config.json")

version_json_url = (
    "https://raw.githubusercontent.com/cedzeedev/cedzeebrowser/refs/heads/main/version.json"
)

def check_first_run():
    if not os.path.exists(CONFIG_FILE):
        config = {"first_run": True}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    else:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        if config.get("first_run", True):
            config["first_run"] = False
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            return True
        else:
            return False

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
if version_online != "error" and version != version_online and version < version_online:
    update_available = True
    try:
        response = requests.get(version_json_url, timeout=10)
        if response.status_code == 200:
            with open(f"{directory}/version_online.json", "w", encoding="utf-8") as f:
                f.write(response.text)
    except Exception:
        pass


class NetworkRequestLogger(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        method = info.requestMethod().data().decode('utf-8')
        resource_type = info.resourceType()

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None, browser_window=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window

    def createWindow(self, _type):
        if self.browser_window:
            new_browser = self.browser_window.open_tab(url_to_load=QUrl())
            return new_browser.page()
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
                if self.browser_window and self.browser_window.current_browser():
                    self.browser_window.current_browser().setUrl(QUrl.fromLocalFile(real_path))
            return False
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)

    def certificateError(self, certificate_error: QWebEngineCertificateError):
        print(f"Erreur de certificat détectée pour {certificate_error.url().toString()}: {certificate_error.errorDescription()}", file=sys.stderr)
        return True
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        return


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ensure_history_file()

        self.setWindowTitle("CEDZEE Browser")
        self.resize(1200, 800)
        self.move(300, 50)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = QListWidget()
        self.sidebar.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.sidebar.model().rowsMoved.connect(self.on_sidebar_rows_moved)
        self.sidebar.setMaximumWidth(200)
        self.sidebar.setMinimumWidth(0)
        self.original_sidebar_width = 200
        self.sidebar.currentRowChanged.connect(self.change_tab_by_sidebar)
        self.main_layout.addWidget(self.sidebar)

        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.sidebar_animation.setDuration(200)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.menu = QToolBar("Menu de navigation")
        self.addToolBar(self.menu)
        self.add_navigation_buttons()
        
        self.create_more_menu()

        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.show_tab_context_menu)

        self._setup_shortcuts()
        self.load_history()

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

        self.add_homepage_tab()

    def _setup_shortcuts(self):
        for seq, fn in [
            ("Ctrl+T", self.open_new_tab),
            ("Ctrl+W", lambda: self.close_tab(self.stacked_widget.currentIndex())),
            ("Ctrl+R", lambda: self.current_browser().reload()),
            ("F5",     lambda: self.current_browser().reload()),
            ("Ctrl+H", self.open_history),
            ("Ctrl+B", self.toggle_sidebar),
        ]:
            a = QAction(self)
            a.setShortcut(seq)
            a.triggered.connect(fn)
            self.addAction(a)

    def on_sidebar_rows_moved(self, parent, start, end, destination, row):
        if start == end:
            w = self.stacked_widget.widget(start)
            self.stacked_widget.removeWidget(w)
            self.stacked_widget.insertWidget(row, w)
            self.stacked_widget.setCurrentIndex(row)

    def change_tab_by_sidebar(self, idx):
        self.stacked_widget.setCurrentIndex(idx)
        b = self.current_browser()
        if b:
            self.update_urlbar(b.url(), b)

    def add_navigation_buttons(self):
        self.fav_dir = os.path.join(directory, "resources", "saves")
        self.fav_file = os.path.join(self.fav_dir, "favorites.json")
        self.fav_icon_add = QIcon(f"{directory}/resources/icons/favorite_add.png")
        self.fav_icon_remove = QIcon(f"{directory}/resources/icons/favorite_remove.png")

        icons = {
            "menu": "menu.png",
            "back": "arrow_back.png",
            "forward": "arrow_forward.png",
            "refresh": "refresh.png",
            "home": "home.png",
            "add": "add.png",
            "dev": "dev.png",
            "history": "history.png",
            "favoris": "favorites.png",
            "more": "more.png",
        }

        for name, fn in [
            ("menu", self.toggle_sidebar),
            ("back", lambda: self.current_browser().back()),
            ("forward", lambda: self.current_browser().forward()),
            ("refresh", lambda: self.current_browser().reload()),
            ("home", self.go_home),
        ]:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

        self.address_input = QLineEdit()
        self.address_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.address_input)

        for name, fn in [
            ("add", self.open_new_tab),
        ]:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

        self.favorite_action = QAction(self.fav_icon_add, "Ajouter aux favoris", self)
        self.favorite_action.setToolTip("Ajouter aux favoris")
        self.favorite_action.triggered.connect(self.toggle_favorite)
        self.menu.addAction(self.favorite_action)

        self.more_button = QToolButton(self)
        self.more_button.setIcon(QIcon(f"{directory}/resources/icons/{icons['more']}"))
        self.more_button.setToolTip("Plus d'options")
        self.more_button.clicked.connect(self.toggle_more_menu)
        self.menu.addWidget(self.more_button)

    def create_more_menu(self):
        self.more_menu = QFrame(self)
        self.more_menu.setObjectName("moreMenu")
        self.more_menu.hide()

        menu_layout = QVBoxLayout(self.more_menu)
        menu_layout.setContentsMargins(4, 4, 4, 4)
        menu_layout.setSpacing(2)

        icons_path = f"{directory}/resources/icons/"
        
        menu_items = [
            ("history", "Historique", self.open_history),
            ("favorites", "Favoris", self.open_favorites),
            ("dev", "Outils de développement", self.open_devtools),
            ("open_in_app", "Ouvrir dans une application", self.open_current_url_in_app),
        ]
        
        for icon, text, func in menu_items:
            btn = QPushButton(QIcon(f"{icons_path}/{icon}.png"), f" {text}")
            btn.clicked.connect(lambda _, f=func: (f(), self.toggle_more_menu()))
            btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            menu_layout.addWidget(btn)

        self.menu_animation = QPropertyAnimation(self.more_menu, b"geometry")
        self.menu_animation.setDuration(200)
        self.menu_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
    def toggle_more_menu(self):
        button_pos = self.more_button.mapTo(self, QPoint(0, self.more_button.height()))
        menu_width = 220
        menu_height = self.more_menu.sizeHint().height()
        
        start_pos_x = button_pos.x() + self.more_button.width() - menu_width
        start_pos_y = button_pos.y()
        
        if self.more_menu.isVisible():
            start_geom = QRect(start_pos_x, start_pos_y, menu_width, menu_height)
            end_geom = QRect(start_pos_x, start_pos_y, menu_width, 0)
            self.menu_animation.finished.connect(self.more_menu.hide)
        else:
            start_geom = QRect(start_pos_x, start_pos_y, menu_width, 0)
            end_geom = QRect(start_pos_x, start_pos_y, menu_width, menu_height)
            self.more_menu.setGeometry(start_geom)
            self.more_menu.show()
            try: self.menu_animation.finished.disconnect() 
            except TypeError: pass

        self.menu_animation.setStartValue(start_geom)
        self.menu_animation.setEndValue(end_geom)
        self.menu_animation.start()

    def toggle_favorite(self):
        browser = self.current_browser()
        if not browser:
            return

        url = browser.url().toString()
        title = browser.title()
        os.makedirs(self.fav_dir, exist_ok=True)

        try:
            with open(self.fav_file, "r", encoding="utf-8") as f:
                favs = json.load(f)
            if not isinstance(favs, list):
                favs = []
        except (FileNotFoundError, json.JSONDecodeError):
            favs = []

        existing = next((item for item in favs if item.get("url") == url), None)
        if existing:
            favs.remove(existing)
            print(f"URL removed from favorites: {url}")
        else:
            favs.append({"url": url, "title": title})
            print(f"URL added to favorites: {url}")

        with open(self.fav_file, "w", encoding="utf-8") as f:
            json.dump(favs, f, indent=4, ensure_ascii=False)

        self.update_favorite_icon(url, favs)

    def update_favorite_icon(self, url=None, favs=None):
        if url is None or favs is None:
            browser = self.current_browser()
            if not browser:
                return
            url = browser.url().toString()
            try:
                with open(self.fav_file, "r", encoding="utf-8") as f:
                    favs = json.load(f)
                if not isinstance(favs, list):
                    favs = []
            except (FileNotFoundError, json.JSONDecodeError):
                favs = []

        is_fav = any(item.get("url") == url for item in favs)
        if is_fav:
            self.favorite_action.setIcon(self.fav_icon_remove)
            self.favorite_action.setToolTip("Retirer des favoris")
        else:
            self.favorite_action.setIcon(self.fav_icon_add)
            self.favorite_action.setToolTip("Ajouter aux favoris")

    def go_home(self):
        if self.current_browser():
            self.current_browser().setUrl(QUrl.fromLocalFile(home_url))

    def toggle_sidebar(self):
        current_width = self.sidebar.maximumWidth()
        if current_width == 0:
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(self.original_sidebar_width)
        else:
            self.sidebar_animation.setStartValue(current_width)
            self.sidebar_animation.setEndValue(0)
        self.sidebar_animation.start()

    def _attach_webchannel(self, browser: QWebEngineView):
        channel = QWebChannel(self)
        bridge = CedzeeBridge(self)
        channel.registerObject("cedzeebrowser", bridge)
        browser.page().setWebChannel(channel)
        bridge.settingChanged.connect(
            lambda k, v: print(f"Setting '{k}' mis à jour en '{v}'")
        )

    def _create_and_configure_browser_tab(self, initial_url: QUrl):
        browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, browser, browser_window=self)
        browser.setPage(page)
        self._attach_webchannel(browser)
        browser.setUrl(initial_url)
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.loadFinished.connect(lambda ok, b=browser: self.handle_load_finished(ok, b))
        return browser

    def add_homepage_tab(self):
        browser = self._create_and_configure_browser_tab(QUrl.fromLocalFile(home_url))
        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Page d'accueil"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    def open_new_tab(self):
        browser = self._create_and_configure_browser_tab(QUrl.fromLocalFile(home_url))
        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Nouvel onglet"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())
        return browser

    def open_welcome_tab(self):
        browser = self._create_and_configure_browser_tab(QUrl.fromLocalFile(welcome_url))
        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Bienvenue"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    def open_tab(self, url_to_load: QUrl):
        if isinstance(url_to_load, str):
            if url_to_load.startswith("cedzee://"):
                target = url_to_load.replace("cedzee://", "")
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
                file_path = mapping.get(target)
                if file_path:
                    url_to_load_obj = QUrl.fromLocalFile(file_path)
                else:
                    print(f"Unknown cedzee:// path: {url_to_load}. Loading home.", file=sys.stderr)
                    url_to_load_obj = QUrl.fromLocalFile(home_url)
            else:
                url_to_load_obj = QUrl(url_to_load)
                if url_to_load_obj.scheme() == "":
                    url_to_load_obj.setScheme("http")
        elif isinstance(url_to_load, QUrl):
            url_to_load_obj = url_to_load
        else:
            print(f"Invalid URL type for open_tab: {type(url_to_load)}. Expected str or QUrl.", file=sys.stderr)
            return None

        if not url_to_load_obj.isValid():
            print(f"Invalid URL provided: {url_to_load_obj.toString()}. Loading offline page.", file=sys.stderr)
            url_to_load_obj = QUrl.fromLocalFile(offline_url)

        browser = self._create_and_configure_browser_tab(url_to_load_obj)
        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Chargement..."))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())
        return browser

    def open_update_tab(self):
        browser = self._create_and_configure_browser_tab(QUrl.fromLocalFile(update_page_url))
        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Mise à jour disponible"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    @staticmethod
    def is_internet_available() -> bool:
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False

    def handle_load_finished(self, ok: bool, browser_instance: QWebEngineView):
        if not ok:
            current_url = browser_instance.url()
            if not current_url.isLocalFile() and current_url.scheme() in ("http", "https"):
                if not BrowserWindow.is_internet_available():
                    print("Pas de connexion Internet détectée. Affichage page offline.", file=sys.stderr)
                    browser_instance.setUrl(QUrl.fromLocalFile(offline_url))
                else:
                    pass

    def open_devtools(self):
        devtools = QWebEngineView()
        devtools.setWindowTitle("DevTools")
        devtools.resize(800, 600)
        devtools.show()
        if self.current_browser():
            self.current_browser().page().setDevToolsPage(devtools.page())
        self.devtools = devtools

    def update_tab_title(self, title, browser_instance):
        idx = self.stacked_widget.indexOf(browser_instance)
        if idx != -1:
            self.sidebar.item(idx).setText(title)

    def current_browser(self):
        return self.stacked_widget.currentWidget()

    def close_tab(self, index):
        if 0 <= index < self.stacked_widget.count() and self.stacked_widget.count() > 1:
            w = self.stacked_widget.widget(index)
            self.stacked_widget.removeWidget(w)
            self.sidebar.takeItem(index)
            w.deleteLater()
            if self.stacked_widget.count() > 0:
                new_index = max(0, index - 1)
                self.stacked_widget.setCurrentIndex(new_index)
                self.sidebar.setCurrentRow(new_index)
                self.update_urlbar(self.current_browser().url(), self.current_browser())

    def navigate_to_url(self):
        text = self.address_input.text().strip()
        cedzee_routes = {
            "cedzee://home": home_url,
            "cedzee://history": history_page_url,
            "cedzee://update": update_page_url,
            "cedzee://offline": offline_url,
            "cedzee://game": game_url,
            "cedzee://welcome": welcome_url,
            "cedzee://contributors": contributors_url,
            "cedzee://favorites": favorites_url,
        }

        if text in cedzee_routes:
            url_to_load = QUrl.fromLocalFile(cedzee_routes[text])
        else:
            url_to_load = QUrl(text)
            if url_to_load.scheme() == "":
                url_to_load = QUrl(f"https://{text}")
                if not url_to_load.isValid():
                    url_to_load = QUrl(f"http://{text}")

        if self.current_browser():
            self.current_browser().setUrl(url_to_load)

    def ensure_history_file(self):
        history_dir = os.path.join(directory, "resources", "config")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def save_to_history(self, url_str: str, title: str):
        if url_str.startswith("http://") or url_str.startswith("https://"):
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

    def open_history(self):
        self.open_tab(QUrl.fromLocalFile(history_page_url))

    def open_favorites(self):
        self.open_tab(QUrl.fromLocalFile(favorites_url))

    def update_urlbar(self, url: QUrl, browser_instance=None):
        if browser_instance != self.current_browser():
            return
        self.address_input.blockSignals(True)
        local_file_urls = {
            QUrl.fromLocalFile(home_url).toString(): "cedzee://home",
            QUrl.fromLocalFile(history_page_url).toString(): "cedzee://history",
            QUrl.fromLocalFile(update_page_url).toString(): "cedzee://update",
            QUrl.fromLocalFile(offline_url).toString(): "cedzee://offline",
            QUrl.fromLocalFile(game_url).toString(): "cedzee://game",
            QUrl.fromLocalFile(welcome_url).toString(): "cedzee://welcome",
            QUrl.fromLocalFile(contributors_url).toString(): "cedzee://contributors",
            QUrl.fromLocalFile(favorites_url).toString(): "cedzee://favorites",
        }
        
        current_url_str = url.toString()
        disp = local_file_urls.get(current_url_str, current_url_str)

        self.address_input.setText(disp)
        self.address_input.setCursorPosition(0)
        self.address_input.blockSignals(False)

        if browser_instance:
            title = browser_instance.title()
            self.save_to_history(disp, title)

        self.update_favorite_icon(current_url_str)

    def show_tab_context_menu(self, pos):
        item = self.sidebar.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        new_tab = menu.addAction("Ouvrir un nouvel onglet")
        close_tab = menu.addAction("Fermer cet onglet")
        action = menu.exec(self.sidebar.mapToGlobal(pos))
        if action == new_tab:
            self.open_new_tab()
        elif action == close_tab:
            idx = self.sidebar.row(item)
            self.close_tab(idx)

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

    def open_current_url_in_app(self):
        current_browser_widget = self.current_browser()
        if current_browser_widget:
            current_url = current_browser_widget.url().toString()
            print(f"Attempting to open URL in external app: {current_url}")
            try:
                start_app(current_url)
                print(f"Successfully called start_app for URL: {current_url}")
            except Exception as e:
                print(f"Error calling AppEngine.start_app: {e}", file=sys.stderr)
        else:
            print("No active browser tab found to get URL from.", file=sys.stderr)


if __name__ == "__main__":
    window = BrowserWindow()
    window.show()
    if check_first_run():
        window.open_welcome_tab()

    if update_available:
        window.open_update_tab()
    application.exec()