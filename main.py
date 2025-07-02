try:

    import os
    import sys

    import requests
    import csv
    from datetime import datetime

    from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve
    from PyQt6.QtGui import QAction
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import (QApplication, QLineEdit, QMainWindow, QMenu, QToolBar, QWidget, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem)

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
        self.setWindowTitle("CEDZEE Browser")
        
        self.resize(1200, 800)
        self.move(300, 50)

        # Main layout for sidebar and content
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove margins

        # Sidebar for tabs
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(200) # Adjust width as needed
        self.sidebar.setMinimumWidth(0) # Allow collapsing
        self.original_sidebar_width = 200 # Store original width
        self.sidebar.currentRowChanged.connect(self.change_tab_by_sidebar)
        self.main_layout.addWidget(self.sidebar) # Add sidebar to the main layout

        # Animation for sidebar
        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.sidebar_animation.setDuration(200) # milliseconds
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Stacked widget for browser views
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.menu = QToolBar("Menu de navigation")
        self.addToolBar(self.menu)
        self.add_navigation_buttons()

        # Context menu for sidebar items (instead of QTabWidget)
        self.sidebar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.show_tab_context_menu)

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

        self.load_history()

        # Load and apply stylesheet
        try:
            with open(os.path.abspath(f"{directory}/theme/theme.css"), "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("theme.css not found.")

        # Add initial homepage tab after stylesheet is loaded
        self.add_homepage_tab()

    def change_tab_by_sidebar(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def add_navigation_buttons(self):

        toggle_sidebar_btn = QAction("☰", self)
        toggle_sidebar_btn.setToolTip("Toggle Sidebar")
        toggle_sidebar_btn.triggered.connect(self.toggle_sidebar)
        self.menu.addAction(toggle_sidebar_btn)

        back_btn = QAction("◀︎", self)
        back_btn.setToolTip("Back")
        back_btn.triggered.connect(lambda: self.current_browser().back() if self.current_browser() else None)
        self.menu.addAction(back_btn)

        forward_btn = QAction("▶︎", self)
        forward_btn.setToolTip("Forward")
        forward_btn.triggered.connect(lambda: self.current_browser().forward() if self.current_browser() else None)
        self.menu.addAction(forward_btn)

        reload_btn = QAction("🔄", self)
        reload_btn.setToolTip("Reload")
        reload_btn.triggered.connect(lambda: self.current_browser().reload() if self.current_browser() else None)
        self.menu.addAction(reload_btn)

        home_btn = QAction("🏠", self)
        home_btn.setToolTip("Home")
        home_btn.triggered.connect(self.go_home)
        self.menu.addAction(home_btn)

        self.address_input = QLineEdit()
        self.address_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.address_input)

        new_tab_btn = QAction("✚", self)
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.triggered.connect(self.open_new_tab)
        self.menu.addAction(new_tab_btn)

        devtools_btn = QAction("🛠️", self)
        devtools_btn.setToolTip("Developer Tools")
        devtools_btn.triggered.connect(self.open_devtools)
        self.menu.addAction(devtools_btn)

        history_btn = QAction("📜", self)
        history_btn.setToolTip("History")
        history_btn.triggered.connect(self.open_history)
        self.menu.addAction(history_btn)

    def toggle_sidebar(self):
        if self.sidebar.maximumWidth() == 0:
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(self.original_sidebar_width)
            self.sidebar_animation.start()
        else:
            self.sidebar_animation.setStartValue(self.original_sidebar_width)
            self.sidebar_animation.setEndValue(0)
            self.sidebar_animation.start()

    def add_homepage_tab(self):

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(home_url))
        self.browser.urlChanged.connect(lambda url, b=self.browser: self.update_urlbar(url))
        self.browser.titleChanged.connect(lambda title, b=self.browser: self.update_tab_title(title, b))
        self.browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(self.browser)
        tab_title = "Page d'accueil"
        item = QListWidgetItem(tab_title)
        self.sidebar.addItem(item)
        self.sidebar.setCurrentItem(item)

    def open_new_tab(self):

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(home_url))
        self.browser.urlChanged.connect(lambda url, b=self.browser: self.update_urlbar(url))
        self.browser.titleChanged.connect(lambda title, b=self.browser: self.update_tab_title(title, b))
        self.browser.page().javaScriptConsoleMessage = self.handle_js_error

        self.stacked_widget.addWidget(self.browser)
        tab_title = "New tab"
        item = QListWidgetItem(tab_title)
        self.sidebar.addItem(item)

        self.stacked_widget.setCurrentWidget(self.browser)
        self.sidebar.setCurrentItem(item)

    def handle_js_error(self, message, line, sourceID, errorMsg):

        print(f"Erreur JavaScript : {message} à la ligne {line} dans {sourceID}: {errorMsg}", file=sys.stderr)

    def open_devtools(self):

        devtools = QWebEngineView()
        devtools.setWindowTitle("DevTools")
        devtools.resize(800, 600)
        devtools.show()
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

        if self.stacked_widget.count() > 1:
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

                response = requests.get('https://google.com')
                response.raise_for_status()
                self.current_browser().setUrl(url)

                self.save_to_history(url.toString())
            except:

                self.current_browser().setUrl(QUrl.fromLocalFile(offline_url))

    def save_to_history(self, url):
        if "file://" not in url:
            with open('history.csv', mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), url])

    def load_history(self):
        try:
            with open('history.csv', mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.history = [row[1] for row in reader]  # On récupère les URLs
                self.history_index = len(self.history) - 1
        except FileNotFoundError:
            self.history = []
            self.history_index = -1

    def open_history(self):
        if self.current_browser():
            self.current_browser().setUrl(QUrl.fromLocalFile(os.path.abspath(f"{directory}/web/history.html")))

    def update_urlbar(self, url):
        if self.stacked_widget.currentWidget() == self.browser:
            self.address_input.setText(url.toString())
            self.address_input.setCursorPosition(0)

            self.save_to_history(url.toString())

    def go_home(self):

        if self.current_browser():

            try:

                response = requests.get('https://google.com')
                response.raise_for_status()
                self.current_browser().setUrl(QUrl.fromLocalFile(home_url))

            except:

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


window = BrowserWindow()
window.show()

application.exec()
