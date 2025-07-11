# Slohwnix 2025
import os
import json
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt, QSize, QDateTime, QUrl, QTimer, pyqtSignal, QObject
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtGui import QIcon, QDesktopServices

directory1 = os.path.dirname(os.path.abspath(__file__))
directory = os.path.dirname(directory1)


class DownloadItemWidget(QFrame):
    def __init__(self, download_item: QWebEngineDownloadRequest, parent=None):
        super().__init__(parent)

        self.download_item = download_item
        self.is_history_item = False
        self.progress_timer = None

        self.setObjectName("downloadItem")

        layout = QHBoxLayout(self)

        self.icon_label = QLabel()
        self.update_icon()
        layout.addWidget(self.icon_label)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.filename_label = QLabel(
            os.path.basename(self.download_item.downloadFileName())
        )
        self.filename_label.setObjectName("fileName")
        info_layout.addWidget(self.filename_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        info_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Démarrage...")
        self.status_label.setObjectName("statusLabel")
        info_layout.addWidget(self.status_label)

        layout.addLayout(info_layout)
        layout.setStretch(1, 1)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("Button")
        self.cancel_button.clicked.connect(self.cancel_download)
        layout.addWidget(self.cancel_button)

        self.open_button = QPushButton("Ouvrir")
        self.open_button.setObjectName("Button")
        self.open_button.clicked.connect(self.open_file)
        self.open_button.hide()
        layout.addWidget(self.open_button)

        self.delete_button = QPushButton("Supprimer")
        self.delete_button.setObjectName("Button")
        self.delete_button.clicked.connect(self.delete_item)
        self.delete_button.hide()
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

        self.download_item.stateChanged.connect(self.update_state)

        self.update_state()

        if (
            self.download_item.state()
            == QWebEngineDownloadRequest.DownloadState.DownloadInProgress
        ):
            self.progress_timer = QTimer(self)
            self.progress_timer.timeout.connect(self._update_progress_from_properties)
            self.progress_timer.start(500)

    def update_icon(self):
        style = self.style()
        icon = style.standardIcon(style.StandardPixmap.SP_FileIcon)
        self.icon_label.setPixmap(icon.pixmap(QSize(32, 32)))

    def sizeHint(self):
        return QSize(super().sizeHint().width(), 80)

    def update_state(self):
        state = self.download_item.state()

        if state == QWebEngineDownloadRequest.DownloadState.DownloadInProgress:
            self.status_label.setText("Téléchargement en cours...")
            self.cancel_button.show()
            self.open_button.hide()
            self.delete_button.hide()
            self.progress_bar.show()
            self._update_progress_from_properties()
            if self.progress_timer is None:
                self.progress_timer = QTimer(self)
                self.progress_timer.timeout.connect(
                    self._update_progress_from_properties
                )
                self.progress_timer.start(500)
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.status_label.setText("Téléchargement terminé")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.cancel_button.hide()
            self.open_button.show()
            self.delete_button.show()
            self.progress_bar.hide()
            if self.progress_timer:
                self.progress_timer.stop()
                self.progress_timer.deleteLater()
                self.progress_timer = None
            if not self.is_history_item:
                parent_manager = self.parentWidget()
                while parent_manager is not None and not isinstance(
                    parent_manager, DownloadManager
                ):
                    parent_manager = parent_manager.parentWidget()
                if isinstance(parent_manager, DownloadManager):
                    parent_manager.save_completed_download(self.download_item)
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            self.status_label.setText("Téléchargement annulé")
            self.progress_bar.hide()
            self.cancel_button.hide()
            self.open_button.hide()
            self.delete_button.show()
            if self.progress_timer:
                self.progress_timer.stop()
                self.progress_timer.deleteLater()
                self.progress_timer = None
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            self.status_label.setText("Téléchargement interrompu")
            self.cancel_button.hide()
            self.open_button.hide()
            self.delete_button.show()
            if self.progress_timer:
                self.progress_timer.stop()
                self.progress_timer.deleteLater()
                self.progress_timer = None

    def _update_progress_from_properties(self):
        bytes_received = self.download_item.receivedBytes()
        bytes_total = self.download_item.totalBytes()

        if bytes_total > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(bytes_received * 100 / bytes_total))
            self.status_label.setText(
                f"Téléchargé {bytes_received / (1024*1024):.2f} Mo / {bytes_total / (1024*1024):.2f} Mo"
            )
        else:
            self.progress_bar.setRange(0, 0)

    def cancel_download(self):
        self.download_item.cancel()

    def open_file(self):
        file_path = self.download_item.downloadFileName()
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            self.status_label.setText(
                "Fichier introuvable. Peut-être déplacé ou supprimé."
            )

    def delete_item(self):
        parent_list_widget = self.parentWidget()
        while parent_list_widget is not None and not isinstance(
            parent_list_widget, QListWidget
        ):
            parent_list_widget = parent_list_widget.parentWidget()

        if isinstance(parent_list_widget, QListWidget):
            for i in range(parent_list_widget.count()):
                item = parent_list_widget.item(i)
                if parent_list_widget.itemWidget(item) is self:
                    row = i
                    parent_list_widget.takeItem(row)
                    break

            if self.is_history_item:
                parent_manager = parent_list_widget.parentWidget()
                while parent_manager is not None and not isinstance(
                    parent_manager, DownloadManager
                ):
                    parent_manager = parent_manager.parentWidget()
                if isinstance(parent_manager, DownloadManager):
                    parent_manager.remove_history_item(
                        self.download_item.downloadFileName()
                    )


class DownloadManager(QWidget):
    DOWNLOAD_HISTORY_FILE = f"{directory}/resources/saves/download_history.json"

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Téléchargements")
        self.setMinimumSize(500, 300)

        self.completed_downloads_history = []

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("downloadListWidget")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.list_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        try:
            css_path = os.path.abspath(f"{directory}/theme/theme.css")
            if os.path.exists(css_path):
                with open(css_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            else:
                print(f"Fichier CSS non trouvé : {css_path}")
        except Exception as e:
            print(f"Impossible de charger le thème pour DownloadManager: {e}")
        os.makedirs(os.path.dirname(self.DOWNLOAD_HISTORY_FILE), exist_ok=True)
        self.load_download_history()

    def add_download(self, download_item: QWebEngineDownloadRequest):
        for i in range(self.list_widget.count()):
            item_widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if (
                isinstance(item_widget, DownloadItemWidget)
                and item_widget.download_item is download_item
            ):
                return

        download_widget = DownloadItemWidget(download_item)
        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(download_widget.sizeHint())
        self.list_widget.insertItem(0, list_item)
        self.list_widget.setItemWidget(list_item, download_widget)
        self.show()

    def save_completed_download(self, download_item: QWebEngineDownloadRequest):
        file_path = download_item.downloadFileName()

        if os.path.exists(file_path):
            download_info = {
                "filename": os.path.basename(file_path),
                "path": file_path,
                "timestamp": QDateTime.currentDateTime().toString(
                    Qt.DateFormat.ISODate
                ),
            }
            if not any(
                item["path"] == download_info["path"]
                for item in self.completed_downloads_history
            ):
                self.completed_downloads_history.append(download_info)
                self._save_history_to_file()
        else:
            print(
                f"Avertissement: Le fichier {file_path} n'existe pas après le téléchargement. Il se peut qu'il ait été déplacé ou que le chemin ne soit pas encore à jour."
            )

    def load_download_history(self):
        if os.path.exists(self.DOWNLOAD_HISTORY_FILE):
            try:
                with open(self.DOWNLOAD_HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.completed_downloads_history = json.load(f)

                for item_info in self.completed_downloads_history:

                    class DummyDownloadRequest(QObject):
                        stateChanged = pyqtSignal()
                        bytesReceived = pyqtSignal(int, int)

                        def __init__(self, filename, path, parent=None):
                            super().__init__(parent)
                            self._filename = filename
                            self._path = path
                            self._state = (
                                QWebEngineDownloadRequest.DownloadState.DownloadCompleted
                            )
                            self.stateChanged.emit()
                            self.bytesReceived.emit(
                                self.receivedBytes(), self.totalBytes()
                            )

                        def downloadFileName(self):
                            return self._path

                        def downloadDirectory(self):
                            return os.path.dirname(self._path)

                        def state(self):
                            return self._state

                        def cancel(self):
                            pass

                        def receivedBytes(self):
                            return (
                                os.path.getsize(self._path)
                                if os.path.exists(self._path)
                                else 0
                            )

                        def totalBytes(self):
                            return (
                                os.path.getsize(self._path)
                                if os.path.exists(self._path)
                                else 0
                            )

                    dummy_download_item = DummyDownloadRequest(
                        item_info["filename"], item_info["path"], parent=self
                    )

                    download_widget = DownloadItemWidget(dummy_download_item)
                    download_widget.is_history_item = True
                    download_widget.progress_timer = None

                    download_widget.cancel_button.hide()
                    download_widget.progress_bar.hide()
                    download_widget.open_button.show()
                    download_widget.delete_button.show()
                    download_widget.status_label.setText(
                        f"Terminé le {item_info['timestamp']}"
                    )

                    list_item = QListWidgetItem(self.list_widget)
                    list_item.setSizeHint(download_widget.sizeHint())
                    self.list_widget.addItem(list_item)
                    self.list_widget.setItemWidget(list_item, download_widget)

            except json.JSONDecodeError as e:
                print(
                    f"Erreur lors du chargement de l'historique des téléchargements: {e}"
                )
                self.completed_downloads_history = []
            except Exception as e:
                print(
                    f"Une erreur inattendue est survenue lors du chargement de l'historique: {e}"
                )
                self.completed_downloads_history = []

    def remove_history_item(self, file_path_to_remove: str):
        self.completed_downloads_history = [
            item
            for item in self.completed_downloads_history
            if item["path"] != file_path_to_remove
        ]
        self._save_history_to_file()

    def _save_history_to_file(self):
        try:
            with open(self.DOWNLOAD_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.completed_downloads_history, f, indent=4)
        except Exception as e:
            print(
                f"Erreur lors de la sauvegarde de l'historique des téléchargements: {e}"
            )
