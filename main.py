# imports
try:
    import os
    import sys
    import requests
    import csv
    import json
    from datetime import datetime

    from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve
    from PyQt6.QtGui import QAction, QIcon
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import (
        QWebEngineProfile,
        QWebEnginePage,
        QWebEngineDownloadRequest,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QLineEdit,
        QMainWindow,
        QMenu,
        QToolBar,
        QWidget,
        QHBoxLayout,
        QStackedWidget,
        QListWidget,
        QListWidgetItem,
        QFileDialog,
    )
except (ImportError, ImportWarning) as err:
    print(f"Import error : {err}")
    Exit_orNot = input("Voulez vous installer les dependances manquantes ? (O/N) : ")
    if Exit_orNot.lower() == "o":
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dépendances installées avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'installation des dépendances : {e}")
    else:
        print("Sortie du programme.")
    exit(1)


# PyQt application setup
application = QApplication.instance()
directory = os.path.dirname(os.path.abspath(__file__))

if not application:
    application = QApplication(sys.argv)

# utils variables
home_url = os.path.abspath(f"{directory}/web/index.html")
history_page_url = os.path.abspath(f"{directory}/web/history.html")
update_page_url = os.path.abspath(f"{directory}/web/update.html")
offline_url = os.path.abspath(f"{directory}/offline/index.html")
game_url = os.path.abspath(f"{directory}/offline/game.html")

version_json_url = (
    "https://raw.githubusercontent.com/cedzeedev/cedzeebrowser/refs/heads/main/version.json"
)

# Load local version information
version_file_pth = f"{directory}/version.json"
try:
    with open(version_file_pth, "r", encoding="utf-8") as file:
        data = json.load(file)
        version = data[0].get("version", "inconnue")
except Exception as e:
    print(f"Erreur lors du chargement de la version : {e}")
    version = "inconnue"


# load online version information
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
    # téléchargement du fichier JSON version
    try:
        response = requests.get(version_json_url, timeout=10)
        if response.status_code == 200:
            with open(f"{directory}/version_online.json", "w", encoding="utf-8") as f:
                f.write(response.text)
    except Exception:
        pass


# web browser
class CustomWebEnginePage(QWebEnginePage):
    """
    Intercepte les clics sur `cedzee://…` pour rediriger vers le fichier local.
    """

    def __init__(self, profile, parent=None, browser_window=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window

    def createWindow(self, _type):
        if self.browser_window:
            new_browser = self.browser_window.open_new_tab()
            return new_browser.page()
        return super().createWindow(_type)

    def acceptNavigationRequest(self, url: QUrl, nav_type, isMainFrame):
        if url.scheme() == "cedzee":
            target = url.toString().replace("cedzee://", "")
            mapping = {
                "home": home_url,
                "history": history_page_url,
                "update": update_page_url,
                "openpoke": offline_url,
            }
            real_path = mapping.get(target)
            if real_path:
                self.browser_window.current_browser().setUrl(QUrl.fromLocalFile(real_path))
            return False
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ensure_history_file()

        # window properties
        self.setWindowTitle("CEDZEE Browser")
        self.resize(1200, 800)
        self.move(300, 50)

        # main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # SIDEBAR
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

        # zone des onglets
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # menu
        self.menu = QToolBar("Menu de navigation")
        self.addToolBar(self.menu)
        self.add_navigation_buttons()

        # context menu du sidebar
        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.show_tab_context_menu)

        # raccourcis
        self._setup_shortcuts()

        # historique
        self.load_history()

        # profil WebEngine
        profile_path = f"{directory}/browser_data"
        self.profile = QWebEngineProfile("Default", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(profile_path)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.downloadRequested.connect(self.on_downloadRequested)

        # thème
        try:
            with open(os.path.abspath(f"{directory}/theme/theme.css"), "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("theme.css not found.")

        # onglet d'accueil
        self.add_homepage_tab()

    def _setup_shortcuts(self):
        for seq, fn in [
            ("Ctrl+T", self.open_new_tab),
            ("Ctrl+W", lambda: self.close_tab(self.stacked_widget.currentIndex())),
            ("Ctrl+R", lambda: self.current_browser().reload()),
            ("F5",   lambda: self.current_browser().reload()),
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
        icons = {
            "menu": "menu.png",
            "back": "arrow_back.png",
            "forward": "arrow_forward.png",
            "refresh": "refresh.png",
            "home": "home.png",
            "add": "add.png",
            "dev": "dev.png",
            "history": "history.png",
        }
        actions = [
            ("menu", self.toggle_sidebar),
            ("back", lambda: self.current_browser().back()),
            ("forward", lambda: self.current_browser().forward()),
            ("refresh", lambda: self.current_browser().reload()),
            ("home", self.go_home),
        ]
        for name, fn in actions:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

        self.address_input = QLineEdit()
        self.address_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.address_input)

        for name, fn in [("add", self.open_new_tab), ("dev", self.open_devtools), ("history", self.open_history)]:
            btn = QAction(QIcon(f"{directory}/resources/icons/{icons[name]}"), "", self)
            btn.setToolTip(name.capitalize())
            btn.triggered.connect(fn)
            self.menu.addAction(btn)

    def go_home(self):
        if self.current_browser():
            try:
                requests.get("https://google.com", timeout=2).raise_for_status()
                self.current_browser().setUrl(QUrl.fromLocalFile(home_url))
            except requests.RequestException:
                self.current_browser().setUrl(QUrl.fromLocalFile(offline_url))

    def toggle_sidebar(self):
        start = 0 if self.sidebar.maximumWidth() else self.original_sidebar_width
        end = self.original_sidebar_width if start == 0 else 0
        self.sidebar_animation.setStartValue(start)
        self.sidebar_animation.setEndValue(end)
        self.sidebar_animation.start()

    def add_homepage_tab(self):
        browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, browser, browser_window=self)
        browser.setPage(page)
        browser.setUrl(QUrl.fromLocalFile(home_url))
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Page d'accueil"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    def open_new_tab(self):
        browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, browser, browser_window=self)
        browser.setPage(page)
        browser.setUrl(QUrl.fromLocalFile(home_url))
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Nouvel onglet"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())
        return browser

    def open_update_tab(self):
        browser = QWebEngineView()
        page = CustomWebEnginePage(self.profile, browser, browser_window=self)
        browser.setPage(page)
        browser.setUrl(QUrl.fromLocalFile(update_page_url))
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(browser)
        self.sidebar.addItem(QListWidgetItem("Mise à jour disponible"))
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentRow(self.stacked_widget.currentIndex())

    def handle_js_error(self, message, line, sourceID, errorMsg):
        print(f"JS Error : {message} line {line} in {sourceID}: {errorMsg}", file=sys.stderr)

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

    def navigate_to_url(self):
        text = self.address_input.text().strip()
        cedzee_routes = {
            "cedzee://home": home_url,
            "cedzee://history": history_page_url,
            "cedzee://update": update_page_url,
            "cedzee://offline": offline_url,
            "cedzee://game": game_url
        }

        if text in cedzee_routes:
            file_path = cedzee_routes[text]
            url = QUrl.fromLocalFile(file_path)
        else:
            url = QUrl(text)
            if url.scheme() == "":
                url.setScheme("http")

        if self.current_browser():
            try:
                requests.get("https://google.com", timeout=2).raise_for_status()
                self.current_browser().setUrl(url)
            except requests.RequestException:
                self.current_browser().setUrl(QUrl.fromLocalFile(offline_url))

    def ensure_history_file(self):
        history_dir = os.path.join(directory, "resources", "config")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

    def save_to_history(self, url_str: str):
        if url_str.startswith("http://") or url_str.startswith("https://"):
            history_path = os.path.join(directory, "resources", "config", "history.csv")
            try:
                with open(history_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url_str]
                    )
            except Exception as e:
                print(f"Erreur lors de l'écriture dans l'historique : {e}")

    def load_history(self):
        try:
            with open(
                f"{directory}/resources/config/history.csv", mode="r", encoding="utf-8"
            ) as f:
                reader = csv.reader(f)
                self.history = [row[1] for row in reader]
                self.history_index = len(self.history) - 1
        except FileNotFoundError:
            self.history = []
            self.history_index = -1

    def open_history(self):
        if self.current_browser():
            self.current_browser().setUrl(QUrl.fromLocalFile(history_page_url))

    def update_urlbar(self, url: QUrl, browser_instance=None):
        if browser_instance != self.current_browser():
            return
        self.address_input.blockSignals(True)
        local = url.toString()
        normalized_home = QUrl.fromLocalFile(home_url).toString()
        normalized_history = QUrl.fromLocalFile(history_page_url).toString()
        normalized_update = QUrl.fromLocalFile(update_page_url).toString()
        normalized_offline = QUrl.fromLocalFile(offline_url).toString()
        normalized_game = QUrl.fromLocalFile(game_url).toString()

        if local == normalized_home:
            disp = "cedzee://home"
        elif local == normalized_history:
            disp = "cedzee://history"
        elif local == normalized_update:
            disp = "cedzee://update"
        elif local == normalized_offline:
            disp = "cedzee://offline"
        elif local == normalized_game:
            disp = "cedzee://game"
        else:
            disp = url.toString()

        self.address_input.setText(disp)
        self.address_input.setCursorPosition(0)
        self.address_input.blockSignals(False)

        self.save_to_history(disp)

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


if __name__ == "__main__":
    window = BrowserWindow()
    window.show()
    if update_available:
        window.open_update_tab()
    application.exec()
