
try:

    import os
    import sys

    import requests
    import csv
    from datetime import datetime

    from PyQt6.QtCore import Qt, QUrl
    from PyQt6.QtGui import QAction
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import (QApplication, QLineEdit, QMainWindow, QMenu, QTabWidget, QToolBar, QVBoxLayout, QWidget)

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

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.menu = QToolBar("Menu de navigation")
        self.addToolBar(self.menu)
        self.add_navigation_buttons()
        self.add_homepage_tab()

        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)

        self.new_tab_shortcut = QAction(self)
        self.new_tab_shortcut.setShortcut("Ctrl+T")
        self.new_tab_shortcut.triggered.connect(self.open_new_tab)
        self.addAction(self.new_tab_shortcut)

        self.close_tab_shortcut = QAction(self)
        self.close_tab_shortcut.setShortcut("Ctrl+W")
        self.close_tab_shortcut.triggered.connect(lambda: self.close_tab(self.tabs.currentIndex()))
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


        self.page_loaded = False 
        self.load_history()

    def add_navigation_buttons(self):

        back_btn = QAction("←", self)
        back_btn.triggered.connect(lambda: self.current_browser().back() if self.current_browser() else None)
        self.menu.addAction(back_btn)

        forward_btn = QAction("→", self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward() if self.current_browser() else None)
        self.menu.addAction(forward_btn)

        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload() if self.current_browser() else None)
        self.menu.addAction(reload_btn)

        home_btn = QAction("⌂", self)
        home_btn.triggered.connect(self.go_home)
        self.menu.addAction(home_btn)

        self.address_input = QLineEdit()
        self.address_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.address_input)

        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(self.open_new_tab)
        self.menu.addAction(new_tab_btn)

        devtools_btn = QAction("DevTools", self)
        devtools_btn.triggered.connect(self.open_devtools)
        self.menu.addAction(devtools_btn)

        history_btn = QAction("Historique", self)
        history_btn.triggered.connect(self.open_history)
        self.menu.addAction(history_btn)


    def add_homepage_tab(self):

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(home_url))
        self.browser.loadFinished.connect(self.on_homepage_loaded)
        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.titleChanged.connect(self.update_tab_title)
        self.browser.page().javaScriptConsoleMessage = self.handle_js_error  

        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Page d'accueil")
        self.tabs.setCurrentWidget(tab)
        self.go_home()


    def update_tab_title(self, title):
        index = self.tabs.currentIndex()
        self.tabs.setTabText(index, title)


    def on_homepage_loaded(self, ok):

        if ok and not self.page_loaded:

            self.browser.reload()
            self.page_loaded = True 


    def current_browser(self):

        current_tab = self.tabs.currentWidget()
        return current_tab.layout().itemAt(0).widget() if current_tab else None


    def close_tab(self, index):

        if self.tabs.count() > 1:
            self.tabs.removeTab(index)


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


    def open_new_tab(self):

        self.add_homepage_tab()


    def show_tab_context_menu(self, position):

        menu = QMenu()
        new_tab_action = menu.addAction("Ouvrir un nouvel onglet")
        close_tab_action = menu.addAction("Fermer cet onglet")

        action = menu.exec(self.tabs.mapToGlobal(position))
        if action == new_tab_action:
            self.open_new_tab()
        elif action == close_tab_action:
            self.close_tab(self.tabs.currentIndex())


    def handle_js_error(self, message, line, sourceID, errorMsg):

        print(f"Erreur JavaScript : {message} à la ligne {line} dans {sourceID}: {errorMsg}", file=sys.stderr)


    def open_devtools(self):

        devtools = QWebEngineView()
        devtools.setWindowTitle("DevTools")
        devtools.resize(800, 600)
        devtools.show()
        self.current_browser().page().setDevToolsPage(devtools.page())
        self.devtools = devtools


window = BrowserWindow()
window.show()

application.exec()
