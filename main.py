import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QAction
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class CedzeeBrowser(QMainWindow):
    """Classe principale pour le navigateur CEDZEE."""

    def __init__(self, local_path):
        """Initialise la fenêtre principale et le navigateur."""
        super().__init__()
        self.local_path = local_path
        self.init_ui()

    def init_ui(self):
        """Initialise l'interface utilisateur."""
        self.setWindowTitle("CEDZEE Browser")
        self.resize(1200, 800)
        self.move(300, 50)

        # Initialise le navigateur web
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl.fromLocalFile(self.local_path))
        self.setCentralWidget(self.browser)

        # Crée la barre d'outils de navigation
        self.create_toolbar()

    def create_toolbar(self):
        """Crée et configure la barre d'outils de navigation."""
        menu = QToolBar("Menu de navigation")
        self.addToolBar(menu)

        # Bouton Précédent
        back_btn = QAction("←", self)
        back_btn.triggered.connect(self.browser.back)
        menu.addAction(back_btn)

        # Bouton Suivant
        forward_btn = QAction("→", self)
        forward_btn.triggered.connect(self.browser.forward)
        menu.addAction(forward_btn)

        # Bouton Recharger
        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(self.browser.reload)
        menu.addAction(reload_btn)

        # Bouton Home
        home_btn = QAction("⌂", self)
        home_btn.triggered.connect(self.go_home)
        menu.addAction(home_btn)

        # Barre d'adresse
        self.adress_input = QLineEdit()
        self.adress_input.returnPressed.connect(self.navigate_to_url)
        self.browser.urlChanged.connect(self.update_address_bar)
        menu.addWidget(self.adress_input)

    def go_home(self):
        """Navigue vers la page d'accueil."""
        self.browser.setUrl(QUrl.fromLocalFile(self.local_path))

    def navigate_to_url(self):
        """Navigue vers l'URL saisie dans la barre d'adresse."""
        url = self.adress_input.text()
        self.browser.setUrl(QUrl(url))

    def update_address_bar(self, url):
        """Met à jour la barre d'adresse avec l'URL actuelle."""
        self.adress_input.setText(url.toString())

def create_application():
    """Crée une instance de QApplication si elle n'existe pas déjà."""
    application = QApplication.instance()
    if not application:
        application = QApplication(sys.argv)
    return application

def load_local_file(file_path):
    """Charge un fichier local et retourne son chemin absolu."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")
    return os.path.abspath(file_path)

def main():
    """Fonction principale pour initialiser et exécuter l'application."""
    application = create_application()
    try:
        local_path = load_local_file("index.html")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    # Crée et affiche la fenêtre principale
    window = CedzeeBrowser(local_path)
    window.show()
    sys.exit(application.exec_())

if __name__ == "__main__":
    main()
