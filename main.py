try:
    import os
    import sys
    import requests
    import csv
    from datetime import datetime

    from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve
    from PyQt6.QtGui import QAction, QIcon
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
    from PyQt6.QtWidgets import (
        QApplication, QLineEdit, QMainWindow, QMenu, QToolBar, QWidget,
        QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem
    )

except (ImportError, ImportWarning) as err:
    print(f"Import error : {err}")
    exit(1)


application = QApplication.instance()
directory = os.path.dirname(os.path.abspath(__file__))

if not application:
    application = QApplication(sys.argv)

home_url = os.path.abspath(f"{directory}/web/index.html")
offline_url = os.path.abspath(f"{directory}/offline/index.html")


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
        # click droit sidebar
        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.show_tab_context_menu)
        # Shortcuts
        self.new_tab_shortcut = QAction(self)
        self.new_tab_shortcut.setShortcut("Ctrl+T")
        self.new_tab_shortcut.triggered.connect(self.open_new_tab)
        self.addAction(self.new_tab_shortcut)

        self.close_tab_shortcut = QAction(self)
        self.close_tab_shortcut.setShortcut("Ctrl+W")
        self.close_tab_shortcut.triggered.connect(lambda: self.close_tab(self.stacked_widget.currentIndex()))
        self.addAction(self.close_tab_shortcut)

        self.reload_shortcut = QAction(self)
        self.reload_shortcut.setShortcut("Ctrl+R")
        self.reload_shortcut.triggered.connect(lambda: self.current_browser().reload() if self.current_browser() else None)
        self.addAction(self.reload_shortcut)

        self.f5_shortcut = QAction(self)
        self.f5_shortcut.setShortcut("F5")
        self.f5_shortcut.triggered.connect(lambda: self.current_browser().reload() if self.current_browser() else None)
        self.addAction(self.f5_shortcut)

        self.open_history_shortcut = QAction(self)
        self.open_history_shortcut.setShortcut("Ctrl+H")
        self.open_history_shortcut.triggered.connect(self.open_history)
        self.addAction(self.open_history_shortcut)

        self.toggle_sidebar_shortcut = QAction(self)
        self.toggle_sidebar_shortcut.setShortcut("Ctrl+B")
        self.toggle_sidebar_shortcut.triggered.connect(self.toggle_sidebar)
        self.addAction(self.toggle_sidebar_shortcut)
        # Load history
        self.load_history()

        profile_path = f"{directory}/browser_data"

        self.profile = QWebEngineProfile("Default", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setCachePath(profile_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)


        try:
            with open(os.path.abspath(f"{directory}/theme/theme.css"), "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("theme.css not found.")

        self.add_homepage_tab()
    def on_sidebar_rows_moved(self, parent, start, end, destination, row):
        if start == end:
            widget = self.stacked_widget.widget(start)
            self.stacked_widget.removeWidget(widget)
            self.stacked_widget.insertWidget(row, widget)
            self.stacked_widget.setCurrentIndex(row)

    def change_tab_by_sidebar(self, index):
        self.stacked_widget.setCurrentIndex(index)
        browser = self.current_browser()
        if browser:
            self.update_urlbar(browser.url(), browser)


    def add_navigation_buttons(self):
        toggle_sidebar_btn = QAction(QIcon(f"{directory}/resources/icons/menu.png"), "", self)
        toggle_sidebar_btn.setToolTip("Toggle Sidebar")
        toggle_sidebar_btn.triggered.connect(self.toggle_sidebar)
        self.menu.addAction(toggle_sidebar_btn)

        back_btn = QAction(QIcon(f"{directory}/resources/icons/arrow_back.png"), "", self)
        back_btn.setToolTip("Back")
        back_btn.triggered.connect(lambda: self.current_browser().back() if self.current_browser() else None)
        self.menu.addAction(back_btn)

        forward_btn = QAction(QIcon(f"{directory}/resources/icons/arrow_forward.png"), "", self)
        forward_btn.setToolTip("Forward")
        forward_btn.triggered.connect(lambda: self.current_browser().forward() if self.current_browser() else None)
        self.menu.addAction(forward_btn)

        reload_btn = QAction(QIcon(f"{directory}/resources/icons/refresh.png"), "", self)
        reload_btn.setToolTip("Reload")
        reload_btn.triggered.connect(lambda: self.current_browser().reload() if self.current_browser() else None)
        self.menu.addAction(reload_btn)

        home_btn = QAction(QIcon(f"{directory}/resources/icons/home.png"), "", self)
        home_btn.setToolTip("Home")
        home_btn.triggered.connect(self.go_home)
        self.menu.addAction(home_btn)

        self.address_input = QLineEdit()
        self.address_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.address_input)

        new_tab_btn = QAction(QIcon(f"{directory}/resources/icons/add.png"), "", self)
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.triggered.connect(self.open_new_tab)
        self.menu.addAction(new_tab_btn)

        devtools_btn = QAction(QIcon(f"{directory}/resources/icons/dev.png"), "", self)
        devtools_btn.setToolTip("Developer Tools")
        devtools_btn.triggered.connect(self.open_devtools)
        self.menu.addAction(devtools_btn)

        history_btn = QAction(QIcon(f"{directory}/resources/icons/history.png"), "", self)
        history_btn.setToolTip("History")
        history_btn.triggered.connect(self.open_history)
        self.menu.addAction(history_btn)

    def toggle_sidebar(self):
        if self.sidebar.maximumWidth() == 0:
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(self.original_sidebar_width)
        else:
            self.sidebar_animation.setStartValue(self.original_sidebar_width)
            self.sidebar_animation.setEndValue(0)
        self.sidebar_animation.start()

    def add_homepage_tab(self):
        browser = QWebEngineView()
        page = QWebEnginePage(self.profile, browser)
        browser.setPage(page)
        browser.setUrl(QUrl.fromLocalFile(home_url))
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(browser)
        item = QListWidgetItem("Page d'accueil")
        self.sidebar.addItem(item)
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentItem(item)

    def open_new_tab(self):
        browser = QWebEngineView()
        page = QWebEnginePage(self.profile, browser)
        browser.setPage(page)
        browser.setUrl(QUrl.fromLocalFile(home_url))
        browser.urlChanged.connect(lambda url, b=browser: self.update_urlbar(url, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(title, b))
        browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(browser)
        item = QListWidgetItem("Nouvel onglet")
        self.sidebar.addItem(item)
        self.stacked_widget.setCurrentWidget(browser)
        self.sidebar.setCurrentItem(item)

    def handle_js_error(self, message, line, sourceID, errorMsg):
        print(f"Erreur JavaScript : {message} à la ligne {line} dans {sourceID}: {errorMsg}", file=sys.stderr)

    def open_devtools(self):
        devtools = QWebEngineView()
        devtools.setWindowTitle("DevTools")
        devtools.resize(800, 600)
        devtools.show()
        if self.current_browser():
            self.current_browser().page().setDevToolsPage(devtools.page())
        self.devtools = devtools

    def update_tab_title(self, title, browser_instance):
        index = self.stacked_widget.indexOf(browser_instance)
        if index != -1:
            item = self.sidebar.item(index)
            if item:
                item.setText(title)

    def current_browser(self):
        return self.stacked_widget.currentWidget()

    def close_tab(self, index):
        if 0 <= index < self.stacked_widget.count() and self.stacked_widget.count() > 1:
            widget_to_remove = self.stacked_widget.widget(index)
            self.stacked_widget.removeWidget(widget_to_remove)
            self.sidebar.takeItem(index)
            widget_to_remove.deleteLater()

    def navigate_to_url(self):
        url = QUrl(self.address_input.text())
        if url.scheme() == "":
            url.setScheme("http")
        if self.current_browser():
            try:
                requests.get('https://google.com', timeout=2).raise_for_status()
                self.current_browser().setUrl(url)
                self.save_to_history(url.toString())
            except requests.RequestException:
                self.current_browser().setUrl(QUrl.fromLocalFile(offline_url))
                
    def ensure_history_file(self):
        history_dir = os.path.join(directory, "resources", "config")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        # Pas besoin de créer le fichier explicitement, 'a' le fera

    def save_to_history(self, url):
        if "file://" not in url:
            history_path = os.path.join(directory, "resources", "config", "history.csv")
            try:
                with open(history_path, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), url])
            except Exception as e:
                print(f"Erreur lors de l'écriture dans l'historique : {e}")

    def load_history(self):
        try:
            with open(f'{directory}/resources/config/history.csv', mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.history = [row[1] for row in reader]
                self.history_index = len(self.history) - 1
        except FileNotFoundError:
            self.history = []
            self.history_index = -1

    def open_history(self):
        if self.current_browser():
            self.current_browser().setUrl(QUrl.fromLocalFile(os.path.abspath(f"{directory}/web/history.html")))

    def update_urlbar(self, url, browser_instance=None):
        if browser_instance == self.current_browser():
            self.address_input.blockSignals(True)
            self.address_input.setText(url.toString())
            self.address_input.setCursorPosition(0)
            self.address_input.blockSignals(False)
            self.save_to_history(url.toString())

    def go_home(self):
        if self.current_browser():
            try:
                requests.get('https://google.com', timeout=2).raise_for_status()
                self.current_browser().setUrl(QUrl.fromLocalFile(home_url))
            except requests.RequestException:
                self.current_browser().setUrl(QUrl.fromLocalFile(offline_url))

    def show_tab_context_menu(self, position):
        item = self.sidebar.itemAt(position)
        if not item:
            return
        menu = QMenu()
        new_tab_action = menu.addAction("Ouvrir un nouvel onglet")
        close_tab_action = menu.addAction("Fermer cet onglet")

        action = menu.exec(self.sidebar.mapToGlobal(position))
        if action == new_tab_action:
            self.open_new_tab()
        elif action == close_tab_action:
            index = self.sidebar.row(item)
            self.close_tab(index)


if __name__ == "__main__":
    window = BrowserWindow()
    window.show()
    application.exec()
