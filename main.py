try:
    
    import sys
    import os
    from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget, QWidget, QMenu, QVBoxLayout
    from PyQt6.QtGui import QAction
    from PyQt6.QtCore import QUrl, Qt
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError as e:
    print(f"Erreur d'importation : {e}")
application = QApplication.instance()
if not application:
    application = QApplication(sys.argv)

home_url = os.path.abspath("./web/index.html")

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

        self.page_loaded = False 

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

        self.adress_input = QLineEdit()
        self.adress_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.adress_input)

        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(self.open_new_tab)
        self.menu.addAction(new_tab_btn)

    def add_homepage_tab(self):
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(home_url))
        self.browser.loadFinished.connect(self.on_homepage_loaded)
        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.page().javaScriptConsoleMessage = self.handle_js_error  

        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Page d'accueil")
        self.tabs.setCurrentWidget(tab)
        self.go_home()

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
        url = QUrl(self.adress_input.text())
        if url.scheme() == "":
            url.setScheme("http")
        if self.current_browser():
            self.current_browser().setUrl(url)

    def update_urlbar(self, url):
        self.adress_input.setText(url.toString())
        self.adress_input.setCursorPosition(0)

    def go_home(self):
        if self.current_browser():
            self.current_browser().setUrl(QUrl.fromLocalFile(home_url))

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

window = BrowserWindow()
window.show()

application.exec()
