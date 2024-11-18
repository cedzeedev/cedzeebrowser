## je vais commenter mon code -> ça vous permet de comprendre à quoi servent mes lignes ;)
#ici j'importe tous les modules nécessaires

import sys
import os

try:

    from PyQt5.QtCore import Qt, QUrl
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtWidgets import (QAction, QApplication, QLineEdit, QMainWindow,
                                 QMenu, QTabWidget, QToolBar, QVBoxLayout,
                                 QWidget)

except (ImportError, ImportWarning) as err:

    print(f"Erreur lors de l'imporation des modules.\nDétails:\n{err}", file=sys.stderr)
    exit(1)

# Vérifie si une instance existe
application = QApplication.instance()
if not application:
    application = QApplication(sys.argv)

# URL de la page d'accueil
home_url = os.path.abspath("./web/index.html")

class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre
        self.setWindowTitle("CEDZEE Browser")
        self.resize(1200, 800)
        self.move(300, 50)

        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # Menu
        self.menu = QToolBar("Menu de navigation")
        self.addToolBar(self.menu)

        # Boutons de navigation
        self.add_navigation_buttons()

        # Premier onglet
        self.add_new_tab(QUrl.fromLocalFile(home_url), "Nouvel Onglet")

        # Menu contextuel
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.show_tab_context_menu)

        # Raccourci clavier pour créer un nouvel onglet
        self.new_tab_shortcut = QAction(self)
        self.new_tab_shortcut.setShortcut("Ctrl+T")
        self.new_tab_shortcut.triggered.connect(self.open_new_tab)
        self.addAction(self.new_tab_shortcut)

    def add_navigation_buttons(self):
        # Bouton Précédent
        back_btn = QAction("←", self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        self.menu.addAction(back_btn)

        # Bouton Suivant
        forward_btn = QAction("→", self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        self.menu.addAction(forward_btn)

        # Bouton Recharger
        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.menu.addAction(reload_btn)

        # Bouton Home
        home_btn = QAction("⌂", self)
        home_btn.triggered.connect(self.go_home)
        self.menu.addAction(home_btn)

        # Barre d'adresse
        self.adress_input = QLineEdit()
        self.adress_input.returnPressed.connect(self.navigate_to_url)
        self.menu.addWidget(self.adress_input)

        # Bouton Nouvel Onglet
        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(self.open_new_tab)
        self.menu.addAction(new_tab_btn)

    def add_new_tab(self, url, label="Nouvel Onglet"):
        browser = QWebEngineView()
        browser.setUrl(url)
        browser.urlChanged.connect(self.update_urlbar)
        browser.loadFinished.connect(lambda: self.tabs.setTabText(self.tabs.currentIndex(), browser.page().title()))

        # Conteneur pour le nouvel onglet
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(browser)
        tab.setLayout(layout)

        self.tabs.addTab(tab, label)
        self.tabs.setCurrentWidget(tab)

    def current_browser(self):
        current_tab = self.tabs.currentWidget()
        return current_tab.layout().itemAt(0).widget()

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        url = QUrl(self.adress_input.text())
        if url.scheme() == "":
            url.setScheme("http")
        self.current_browser().setUrl(url)

    def update_urlbar(self, url):
        self.adress_input.setText(url.toString())
        self.adress_input.setCursorPosition(0)

    def go_home(self):
        self.current_browser().setUrl(QUrl.fromLocalFile(home_url))

    def open_new_tab(self):
        self.add_new_tab(QUrl.fromLocalFile(home_url), "Nouvel Onglet")

    def show_tab_context_menu(self, position):
        menu = QMenu()
        new_tab_action = menu.addAction("Ouvrir un nouvel onglet")
        close_tab_action = menu.addAction("Fermer cet onglet")

        action = menu.exec_(self.tabs.mapToGlobal(position))
        if action == new_tab_action:
            self.open_new_tab()
        elif action == close_tab_action:
            self.close_tab(self.tabs.currentIndex())

# Lancement de la fenêtre principale
window = BrowserWindow()
window.show()

# Exécution de l'application
application.exec_()
