import os
import json

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineCertificateError,
)

from src.ConsoleLogger import logger

# Get project root directory
directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace(
    "\\", "/"
)

# Define mapping for cedzee:// URLs to local files
mapping_urls = {
    "home": os.path.abspath(f"{directory}/web/index.html"),
    "history": os.path.abspath(f"{directory}/web/history.html"),
    "update": os.path.abspath(f"{directory}/web/update.html"),
    "offline": os.path.abspath(f"{directory}/offline/index.html"),
    "game": os.path.abspath(f"{directory}/offline/game.html"),
    "welcome": os.path.abspath(f"{directory}/web/welcome.html"),
    "favorites": os.path.abspath(f"{directory}/web/favorites.html"),
    "settings": os.path.abspath(f"{directory}/web/settings.html"),
}


def get_enabled_extensions(current_url):
    """
    Returns a list of extension script paths to inject for the given URL.
    """
    extensions_dir = os.path.join(directory, "extensions")
    scripts = []
    
    if not os.path.exists(extensions_dir):
        logger.warning(f"Extensions directory not found: {extensions_dir}")
        return scripts

    for ext_name in os.listdir(extensions_dir):
        ext_path = os.path.join(extensions_dir, ext_name)
        config_path = os.path.join(ext_path, "config.json")
        main_js_path = os.path.join(ext_path, "main.js")

        if not (
            os.path.isdir(ext_path)
            and os.path.isfile(config_path)
            and os.path.isfile(main_js_path)
        ):
            continue

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            if config.get("disabled", False):
                continue

            # Check enabled_for/disabled_for
            enabled_for = config.get("enabled_for", [])
            disabled_for = config.get("disabled_for", [])

            if enabled_for and not any(
                current_url.startswith(url) for url in enabled_for
            ):
                continue
            if any(current_url.startswith(url) for url in disabled_for):
                continue
            # Use relative path for injection
            scripts.append(f"{directory}/extensions/{ext_name}/main.js")

        except Exception as err:
            logger.error(f"Error loading extension {ext_name}: {err}")
            continue

    return scripts


class CustomWebEnginePage(QWebEnginePage):
    """Custom page for handling cedzee:// navigation."""

    def __init__(self, profile, parent=None, browser_window=None, open_as="web"):
        super().__init__(profile, parent)
        self.browser_window = browser_window
        self.open_as = open_as

    def createWindow(self, _type):
        if self.open_as == "app":
            if self.browser_window and self.browser_window.browser:
                return self.browser_window.browser.page()
        else:
            if self.browser_window:
                new_browser = self.browser_window.open_tab(url_to_load=QUrl())
                return new_browser.page()
        return super().createWindow(_type)

    def acceptNavigationRequest(self, url: QUrl, nav_type, isMainFrame):
        """Handle navigation requests, especially for cedzee:// URLs."""
        if url.scheme() == "cedzee":
            target = url.toString().replace("cedzee://", "")
            real_path = mapping_urls.get(target)

            if self.open_as == "app":
                if real_path:
                    self.setUrl(QUrl.fromLocalFile(real_path))
                else:
                    logger.error(
                        f"Unknown cedzee:// path: {url.toString()}. Loading home."
                    )
                self.setUrl(QUrl.fromLocalFile(mapping_urls["home"]))

            else:
                if (
                    real_path
                    and self.browser_window
                    and self.browser_window.current_browser()
                ):
                    self.browser_window.current_browser().setUrl(
                        QUrl.fromLocalFile(real_path)
                    )

            return False

        return super().acceptNavigationRequest(url, nav_type, isMainFrame)

    def inject_extensions(self, url):
        """Injects enabled extensions for the current URL."""
        if self.open_as != "web":
            return

        logger.info(f"Injecting extensions for URL: {url.toString()}")
        scripts = get_enabled_extensions(url.toString())

        for script_path in scripts:
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    self.runJavaScript(file.read())
            except Exception as err:
                logger.error(f"Failed to inject script {script_path}: {err}")

    def certificateError(self, certificate_error: QWebEngineCertificateError):
        # Optionally handle certificate errors here
        pass

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Optionally handle JS console messages here
        pass
