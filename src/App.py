import os
import sys
import csv
import json
import ctypes
import requests

from urllib.parse import urlparse, quote
from datetime import datetime

from src.AppEngine import start_app
from src.Bridge import CedzeeBridge
from src.ConsoleLogger import logger
from src.CustomWebEnginePage import CustomWebEnginePage, directory, mapping_urls
from src.DownloadManager import DownloadManager

from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import (
    Qt,
    QUrl,
    QPropertyAnimation,
    QEasingCurve,
    QObject,
    pyqtSlot,
    QRect,
    QPoint,
    qInstallMessageHandler,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
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
    QToolButton,
)

# Set Windows AppUserModelID for proper taskbar grouping
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "Cedzeedev.Cedzeebrowser.release.1_0"
    )


def message_handler(mode, context, message):
    # Ignore geometry warnings, log others
    if "QWindowsWindow::setGeometry" in message:
        return
    logger.error(message)


qInstallMessageHandler(message_handler)

# Set Chromium flags for performance
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-gpu --enable-webgl --enable-accelerated-2d-canvas "
    "--ignore-gpu-blocklist --enable-zero-copy --disable-software-rasterizer "
    "--use-gl=angle --enable-native-gpu-memory-buffers"
)

# Ensure QApplication instance
application = QApplication.instance() or QApplication(sys.argv)


class FirstRunWorker(QObject):
    """Worker to check and handle first run logic."""

    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config_file = os.path.abspath(f"{directory}/resources/config.json")

    @pyqtSlot()
    def check(self):
        try:
            if not os.path.exists(self.config_file):
                config = {"first_run": False}
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                self.finished.emit(True)
                return
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            if config.get("first_run", True):
                config["first_run"] = False
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                self.finished.emit(True)
            else:
                self.finished.emit(False)
        except Exception as e:
            self.error.emit(
                f"Erreur lors de la vérification du premier lancement : {e}"
            )
            self.finished.emit(False)


class UpdateCheckWorker(QObject):
    """Worker to check for application updates."""

    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.version_json_url = "https://raw.githubusercontent.com/cedzeedev/cedzeebrowser/refs/heads/main/version.json"
        self.version_file_path = f"{directory}/version.json"

    @pyqtSlot()
    def check(self):
        try:
            with open(self.version_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            local_version = data[0].get("version", "inconnue")
            response = requests.get(self.version_json_url, timeout=10)
            response.raise_for_status()
            online_version = response.json()[0].get("version", "inconnue")
            if (
                online_version != "error"
                and local_version != "inconnue"
                and local_version < online_version
            ):
                with open(
                    f"{directory}/version_online.json", "w", encoding="utf-8"
                ) as f:
                    f.write(response.text)
                self.finished.emit(True)
            else:
                self.finished.emit(False)
        except Exception as e:
            self.error.emit(f"Erreur lors de la vérification de mise à jour : {e}")
            self.finished.emit(False)


class AdBlockerWorker(QObject):
    """Worker to load ad block list from online or local source."""

    list_loaded = pyqtSignal(set)
    error = pyqtSignal(str)

    @pyqtSlot()
    def load_list(self):
        AD_BLOCK_LIST_URL = (
            "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt"
        )
        block_list = set()
        try:
            response = requests.get(AD_BLOCK_LIST_URL, timeout=10)
            response.raise_for_status()
            for line in response.text.splitlines():
                line = line.strip()
                if not line or line.startswith("!") or line.startswith("@@"):
                    continue
                if line.startswith("||"):
                    domain = line[2:].split("^")[0]
                    if domain:
                        block_list.add(domain.lower())
            self.list_loaded.emit(block_list)
        except Exception as e:
            self.error.emit(f"[AdBlock] Échec du chargement en ligne : {e}")
            block_list_path = os.path.join(directory, "resources", "ad_block_list.txt")
            try:
                with open(block_list_path, "r", encoding="utf-8") as f:
                    local_block_list = {
                        line.strip().lower() for line in f if line.strip()
                    }
                self.list_loaded.emit(local_block_list)
            except FileNotFoundError:
                self.error.emit(
                    f"[AdBlock] Liste locale introuvable : {block_list_path}"
                )
                self.list_loaded.emit(set())


class AdBlockerRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercepts requests and blocks domains in block list."""

    def __init__(self, parent=None, block_list=None, browser_window=None):
        super().__init__(parent)
        self.block_list = block_list or set()
        self.browser_window = browser_window

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if not (self.browser_window and self.browser_window.ad_blocker_enabled):
            return
        host = info.requestUrl().host().lower()
        if host.startswith("www."):
            host = host[4:]
        for blocked_domain in self.block_list:
            if host == blocked_domain or host.endswith("." + blocked_domain):
                info.block(True)
                return


class BrowserWindow(QMainWindow):
    """Main browser window with tab, sidebar, adblock, and navigation."""

    def __init__(self):
        super().__init__()
        self.ensure_history_file()
        self.setWindowTitle("CEDZEE Browser")
        self.resize(1200, 800)
        self.center()
        icon_path = f"{directory}/resources/icons/icon.png"
        try:
            self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.error(f"Error loading the icon : {e}")

        self.app_windows = []
        self.download_manager = DownloadManager()
        self.ad_blocker_enabled = False
        self.ad_block_list = set()

        # Layout setup
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar for tabs
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

        # Tab stack
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Navigation menu
        self.menu = QToolBar("Menu de navigation")
        self.menu.setEnabled(True)
        self.menu.setVisible(True)
        self.menu.setFixedHeight(50)
        self.menu.setAllowedAreas(
            Qt.ToolBarArea.TopToolBarArea | Qt.ToolBarArea.BottomToolBarArea
        )
        self.addToolBar(self.menu)
        self.add_navigation_buttons()
        self.create_more_menu()

        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.show_tab_context_menu)

        self._setup_shortcuts()
        self.load_history()

        # Web profile setup
        profile_path = f"{directory}/browser_data"
        self.profile = QWebEngineProfile("Default", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(profile_path)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.downloadRequested.connect(self.on_downloadRequested)

        self.request_interceptor = None
        self.threads = []

        # Apply theme
        try:
            css_path = os.path.abspath(f"{directory}/theme/browser.css")
            with open(css_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger.error("browser.css not found.")

        self.add_homepage_tab()
        self.start_background_tasks()

    def start_background_tasks(self):
        """Start threads for first run, update check, and adblock list."""

        def setup_worker(worker, thread, finished_slot):
            worker.moveToThread(thread)
            thread.started.connect(
                worker.check if hasattr(worker, "check") else worker.load_list
            )
            (
                worker.finished.connect(finished_slot)
                if hasattr(worker, "finished")
                else None
            )
            worker.error.connect(lambda msg: logger.error(msg))
            (
                worker.finished.connect(thread.quit)
                if hasattr(worker, "finished")
                else None
            )
            (
                worker.finished.connect(worker.deleteLater)
                if hasattr(worker, "finished")
                else None
            )
            thread.finished.connect(thread.deleteLater)
            thread.start()
            self.threads.append(thread)

        self.first_run_thread = QThread()
        self.first_run_worker = FirstRunWorker()
        setup_worker(
            self.first_run_worker,
            self.first_run_thread,
            self.on_first_run_check_finished,
        )

        self.update_check_thread = QThread()
        self.update_check_worker = UpdateCheckWorker()
        setup_worker(
            self.update_check_worker,
            self.update_check_thread,
            self.on_update_check_finished,
        )

        self.adblock_thread = QThread()
        self.adblock_worker = AdBlockerWorker()
        self.adblock_worker.list_loaded.connect(self.on_adblock_list_loaded)
        self.adblock_worker.list_loaded.connect(self.adblock_thread.quit)
        self.adblock_worker.list_loaded.connect(self.adblock_worker.deleteLater)
        self.adblock_thread.finished.connect(self.adblock_thread.deleteLater)
        self.adblock_worker.error.connect(lambda msg: logger.error(msg))
        self.adblock_worker.moveToThread(self.adblock_thread)
        self.adblock_thread.started.connect(self.adblock_worker.load_list)
        self.adblock_thread.start()
        self.threads.append(self.adblock_thread)

    @pyqtSlot(bool)
    def on_first_run_check_finished(self, is_first_run):
        if is_first_run:
            self.open_welcome_tab()

    @pyqtSlot(bool)
    def on_update_check_finished(self, is_update_available):
        if is_update_available:
            self.open_update_tab()

    @pyqtSlot(set)
    def on_adblock_list_loaded(self, block_list):
        self.ad_block_list = block_list
        self.request_interceptor = AdBlockerRequestInterceptor(
            block_list=self.ad_block_list, browser_window=self
        )
        self.profile.setUrlRequestInterceptor(self.request_interceptor)
        logger.info(
            f"ADBLOCK: {len(self.ad_block_list)} domains loaded in the block list."
        )

    def contextMenuEvent(self, event):
        event.ignore()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for navigation and actions."""
        shortcuts = [
            ("Ctrl+T", self.open_new_tab),
            ("Ctrl+W", lambda: self.close_tab(self.stacked_widget.currentIndex())),
            ("Ctrl+R", lambda: self.current_browser().reload()),
            ("F5", lambda: self.current_browser().reload()),
            ("Ctrl+H", self.open_history),
            ("Ctrl+J", self.download_manager.show),
            ("Ctrl+B", self.toggle_sidebar),
        ]
        for seq, fn in shortcuts:
            a = QAction(self)
            a.setShortcut(seq)
            a.triggered.connect(fn)
            self.addAction(a)

    def on_sidebar_rows_moved(self, parent, start, end, destination, row):
        """Handle sidebar tab reordering."""
        if start == end:
            w = self.stacked_widget.widget(start)
            self.stacked_widget.removeWidget(w)
            self.stacked_widget.insertWidget(row, w)
            self.stacked_widget.setCurrentIndex(row)

    def change_tab_by_sidebar(self, idx):
        """Switch tab when sidebar selection changes."""
        if 0 <= idx < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(idx)
            b = self.current_browser()
            if b:
                self.update_urlbar(b.url(), b)

    def center(self):
        """Center window on screen."""
        screen_geometry = self.screen().geometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def add_navigation_buttons(self):
        """Add navigation buttons and address bar to toolbar."""
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

        nav_actions = [
            ("menu", self.toggle_sidebar),
            ("back", lambda: self.current_browser().back()),
            ("forward", lambda: self.current_browser().forward()),
            ("refresh", lambda: self.current_browser().reload()),
            ("home", self.go_home),
        ]

        for name, fn in nav_actions:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

        self.address_input = QLineEdit()
        self.address_input.setMinimumWidth(200)
        self.address_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.address_input)

        add_tab_btn = QAction(
            QIcon(f"{directory}/resources/icons/{icons['add']}"), "", self
        )
        add_tab_btn.setToolTip("Add")
        add_tab_btn.triggered.connect(self.open_new_tab)

        self.menu.addAction(add_tab_btn)
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
        """Create the 'more' menu with extra actions."""
        self.more_menu = QFrame(self)
        self.more_menu.setObjectName("moreMenu")
        self.more_menu.hide()

        menu_layout = QVBoxLayout(self.more_menu)
        menu_layout.setContentsMargins(4, 4, 4, 4)
        menu_layout.setSpacing(2)

        icons_path = f"{directory}/resources/icons/"

        self.adblock_icon_on = QIcon(f"{icons_path}adblock_on.png")
        self.adblock_icon_off = QIcon(f"{icons_path}adblock_off.png")
        self.ad_blocker_button = QPushButton()
        self.ad_blocker_button.clicked.connect(self.toggle_ad_blocker)
        self.ad_blocker_button.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        menu_layout.addWidget(self.ad_blocker_button)

        self.update_ad_blocker_button_ui()

        menu_items = [
            ("history", "Historique", self.open_history),
            ("favorites", "Favoris", self.open_favorites),
            ("download", "Téléchargements", self.download_manager.show),
            ("dev", "Outils de développement", self.open_devtools),
            (
                "open_in_app",
                "Ouvrir dans une application",
                self.open_current_url_in_app,
            ),
            ("settings", "Paramètres", self.open_settings),
        ]

        for icon, text, func in menu_items:
            icon_path = f"{icons_path}/{icon}.png"
            btn = (
                QPushButton(QIcon(icon_path), f" {text}")
                if os.path.exists(icon_path)
                else QPushButton(f" {text}")
            )
            btn.clicked.connect(lambda _, f=func: (f(), self.toggle_more_menu()))
            btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            menu_layout.addWidget(btn)

        self.menu_animation = QPropertyAnimation(self.more_menu, b"geometry")
        self.menu_animation.setDuration(200)
        self.menu_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle_ad_blocker(self):
        """Enable/disable ad blocker."""
        self.ad_blocker_enabled = not self.ad_blocker_enabled
        self.update_ad_blocker_button_ui()

        logger.info(
            f"ADBLOCK: Ad blocker {'enabled' if self.ad_blocker_enabled else 'disabled'}"
        )

        if self.current_browser():
            self.current_browser().reload()
        self.toggle_more_menu()

    def update_ad_blocker_button_ui(self):
        """Update ad blocker button UI."""
        if self.ad_blocker_enabled:
            self.ad_blocker_button.setText(" Bloqueur de pub (Activé)")
            self.ad_blocker_button.setIcon(self.adblock_icon_on)
        else:
            self.ad_blocker_button.setText(" Bloqueur de pub (Désactivé)")
            self.ad_blocker_button.setIcon(self.adblock_icon_off)

    def toggle_more_menu(self):
        """Show/hide the more menu with animation."""
        button_pos = self.more_button.mapTo(self, QPoint(0, self.more_button.height()))
        menu_width, menu_height = 220, self.more_menu.sizeHint().height()

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

            try:
                self.menu_animation.finished.disconnect()
            except TypeError:
                pass

        self.menu_animation.setStartValue(start_geom)
        self.menu_animation.setEndValue(end_geom)
        self.menu_animation.start()

    def toggle_favorite(self):
        """Add/remove current page from favorites."""
        browser = self.current_browser()
        if not browser:
            return

        url, title = browser.url().toString(), browser.title()
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
        else:
            favs.append({"url": url, "title": title})

        with open(self.fav_file, "w", encoding="utf-8") as f:
            json.dump(favs, f, indent=4, ensure_ascii=False)
        self.update_favorite_icon(url, favs)

    def update_favorite_icon(self, url=None, favs=None):
        """Update favorite icon based on current page."""
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
        """Navigate to home page."""
        if self.current_browser():
            self.current_browser().setUrl(QUrl.fromLocalFile(mapping_urls["home"]))

    def toggle_sidebar(self):
        """Show/hide sidebar with animation."""
        current_width = self.sidebar.maximumWidth()

        self.sidebar_animation.setStartValue(current_width)
        self.sidebar_animation.setEndValue(
            self.original_sidebar_width if current_width == 0 else 0
        )
        self.sidebar_animation.start()

    def _attach_webchannel(self, browser: QWebEngineView):
        """Attach JS/Python bridge to browser tab."""
        channel = QWebChannel(self)
        bridge = CedzeeBridge(self)
        bridge.set_web_profile(self.profile)
        bridge.set_web_page(browser.page())
        channel.registerObject("cedzeebrowser", bridge)
        browser.page().setWebChannel(channel)
        bridge.settingChanged.connect(
            lambda k, v: logger.info(f"Setting '{k}' update on '{v}'")
        )

    def _create_and_configure_browser_tab(self, initial_url: QUrl):
        """Create a browser tab and configure signals."""
        browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, browser, browser_window=self)
        browser.setPage(page)
        self._attach_webchannel(browser)

        browser.setUrl(initial_url)
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(
            lambda title, b=browser: self.update_tab_title(title, b)
        )
        browser.loadFinished.connect(
            lambda ok, b=browser: self.handle_load_finished(ok, b)
        )
        # Inject extensions after every page load
        browser.loadFinished.connect(
            lambda ok, b=browser: page.inject_extensions(b.url())
        )

        return browser

    def add_homepage_tab(self):
        """Add homepage tab on startup."""
        browser = self._create_and_configure_browser_tab(
            QUrl.fromLocalFile(mapping_urls["home"])
        )

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Page d'accueil"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    def open_new_tab(self):
        """Open a new tab with homepage."""
        browser = self._create_and_configure_browser_tab(
            QUrl.fromLocalFile(mapping_urls["home"])
        )

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Nouvel onglet"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

        return browser

    def open_welcome_tab(self):
        """Open welcome tab (first run)."""
        browser = self._create_and_configure_browser_tab(
            QUrl.fromLocalFile(mapping_urls["welcome"])
        )

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Bienvenue"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    def open_tab(self, url_to_load: QUrl):
        """Open a new tab with given URL or cedzee route."""
        if isinstance(url_to_load, str):
            if url_to_load.startswith("cedzee://"):
                target = url_to_load.replace("cedzee://", "")
                file_path = mapping_urls.get(target)
                url_to_load_obj = QUrl.fromLocalFile(
                    file_path if file_path else mapping_urls["home"]
                )
            else:
                url_to_load_obj = QUrl(url_to_load)
                if url_to_load_obj.scheme() == "":
                    url_to_load_obj.setScheme("http")
        elif isinstance(url_to_load, QUrl):
            url_to_load_obj = url_to_load
        else:
            return None

        if not url_to_load_obj.isValid():
            url_to_load_obj = QUrl.fromLocalFile(mapping_urls["offline"])

        browser = self._create_and_configure_browser_tab(url_to_load_obj)

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Chargement..."))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

        return browser

    def open_update_tab(self):
        """Open update tab if update available."""
        browser = self._create_and_configure_browser_tab(
            QUrl.fromLocalFile(mapping_urls["update"])
        )

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Mise à jour disponible"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    @staticmethod
    def is_internet_available():
        """Check internet connectivity."""
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False

    def handle_load_finished(self, ok, browser_instance):
        """Handle page load finished event."""
        if not ok and not browser_instance.url().isLocalFile():
            if not self.is_internet_available():
                browser_instance.setUrl(QUrl.fromLocalFile(mapping_urls["offline"]))

    def open_devtools(self):
        """Open DevTools window for debugging."""
        devtools = QWebEngineView()
        devtools.setWindowTitle("DevTools")
        devtools.resize(800, 600)
        devtools.show()

        if self.current_browser():
            self.current_browser().page().setDevToolsPage(devtools.page())
        self.devtools = devtools

    def update_tab_title(self, title, browser_instance):
        """Update sidebar tab title."""
        idx = self.stacked_widget.indexOf(browser_instance)
        if idx != -1:
            self.sidebar.item(idx).setText(title)

    def current_browser(self):
        """Get current browser tab."""
        return self.stacked_widget.currentWidget()

    def close_tab(self, index):
        """Close tab at given index."""
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
        """Navigate to URL entered in address bar."""
        text = self.address_input.text().strip()

        cedzee_routes = {
            "cedzee://home": mapping_urls["home"],
            "cedzee://history": mapping_urls["history"],
            "cedzee://update": mapping_urls["update"],
            "cedzee://offline": mapping_urls["offline"],
            "cedzee://game": mapping_urls["game"],
            "cedzee://welcome": mapping_urls["welcome"],
            "cedzee://favorites": mapping_urls["favorites"],
            "cedzee://settings": mapping_urls["settings"],
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
        """Ensure history file directory exists."""
        history_dir = os.path.join(directory, "resources", "saves")
        os.makedirs(history_dir, exist_ok=True)

    def save_to_history(self, url_str, title):
        """Save visited URL and title to history."""
        if (
            url_str.startswith("http")
            and title
            and not title.startswith("http")
            and title != "Chargement..."
        ):
            history_path = os.path.join(directory, "resources", "saves", "history.csv")
            try:
                with open(history_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url_str, title]
                    )
            except Exception:
                pass

    def load_history(self):
        """Load history from file."""
        try:
            with open(
                f"{directory}/resources/saves/history.csv", mode="r", encoding="utf-8"
            ) as f:
                reader = csv.reader(f)
                self.history = [row[1] for row in reader if len(row) > 1]
        except FileNotFoundError:
            self.history = []

    def open_history(self):
        """Open history tab."""
        self.open_tab(QUrl.fromLocalFile(mapping_urls["history"]))

    def open_favorites(self):
        """Open favorites tab."""
        self.open_tab(QUrl.fromLocalFile(mapping_urls["favorites"]))

    def open_settings(self):
        """Open settings tab."""
        self.open_tab(QUrl.fromLocalFile(mapping_urls["settings"]))

    def update_urlbar(self, url, browser_instance=None):
        """Update address bar and save history."""
        if browser_instance != self.current_browser():
            return

        self.address_input.blockSignals(True)

        local_file_urls = {
            QUrl.fromLocalFile(mapping_urls["home"]).toString(): "cedzee://home",
            QUrl.fromLocalFile(
                mapping_urls["history"]
            ).toString(): "cedzee://history",
            QUrl.fromLocalFile(
                mapping_urls["update"]
            ).toString(): "cedzee://update",
            QUrl.fromLocalFile(
                mapping_urls["offline"]
            ).toString(): "cedzee://offline",
            QUrl.fromLocalFile(mapping_urls["game"]).toString(): "cedzee://game",
            QUrl.fromLocalFile(
                mapping_urls["welcome"]
            ).toString(): "cedzee://welcome",
            QUrl.fromLocalFile(
                mapping_urls["favorites"]
            ).toString(): "cedzee://favorites",
            QUrl.fromLocalFile(
                mapping_urls["settings"]
            ).toString(): "cedzee://settings",
        }

        current_url_str = url.toString()
        dis = local_file_urls.get(current_url_str, current_url_str)

        self.address_input.setText(dis)
        self.address_input.setCursorPosition(0)
        self.address_input.blockSignals(False)

        if browser_instance:
            self.save_to_history(dis, browser_instance.title())

        self.update_favorite_icon(current_url_str)

    def show_tab_context_menu(self, pos):
        """Show context menu for sidebar tabs."""
        item = self.sidebar.itemAt(pos)
        menu = QMenu(self)
        new_tab_action = menu.addAction("Ouvrir un nouvel onglet")
        close_tab_action = menu.addAction("Fermer cet onglet") if item else None
        action = menu.exec(self.sidebar.mapToGlobal(pos))

        if action == new_tab_action:
            self.open_new_tab()
        elif action == close_tab_action and item:
            self.close_tab(self.sidebar.row(item))

    def on_downloadRequested(self, download_item):
        """Handle download requests."""
        suggested = download_item.suggestedFileName() or "downloaded_file"
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_path, exist_ok=True)
        initial_save_path = os.path.join(downloads_path, os.path.basename(suggested))
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le fichier", initial_save_path
        )

        if not path:
            download_item.cancel()
            return

        download_item.setDownloadFileName(path)
        download_item.accept()
        self.download_manager.add_download(download_item)

    def open_current_url_in_app(self):
        """Open current URL in a new app window."""
        browser = self.current_browser()
        if browser:
            try:
                new_window = start_app(browser.url().toString())
                self.app_windows.append(new_window)
            except Exception as e:
                logger.error(f"Error when opening in the application : {e}")

    def closeEvent(self, event):
        """Clean up all running threads before closing"""
        for thread in getattr(self, "threads", []):
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait()
            except:
                pass
        super().closeEvent(event)


def path_to_uri(path):
    """Convert file path to file URI."""
    path = os.path.abspath(path).replace("\\", "/")
    logger.info(f"{path=}")
    return (
        "file:///" + quote(path)
        if sys.platform == "Windows"
        else "file://" + quote(path)
    )


def is_url(string):
    """Check if string is a valid HTTP/HTTPS URL."""
    try:
        parsed = urlparse(string)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def main():
    """Main entry point for the browser app."""
    if len(sys.argv) <= 1:
        window = BrowserWindow()
        window.show()
        sys.exit(application.exec())
    else:
        file = sys.argv[1]
        app_window = None
        if is_url(file):
            app_window = start_app(file)
        elif file.endswith((".html", ".cedapp")):
            app_window = start_app(path_to_uri(file))
        else:
            logger.error("Unsupported file or unknown format.")
            sys.exit(1)
        if app_window:
            sys.exit(application.exec())


if __name__ == "__main__":
    application = QApplication.instance() or QApplication(sys.argv)
    main()
