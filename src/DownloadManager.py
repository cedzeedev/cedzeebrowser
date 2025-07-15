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
from PyQt6.QtCore import (
    Qt,
    QSize,
    QDateTime,
    QUrl,
    pyqtSignal,
    QObject,
    QThread,
    pyqtSlot,
)
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtGui import QIcon, QDesktopServices

directory1 = os.path.dirname(os.path.abspath(__file__))
directory = os.path.dirname(directory1)


class DownloadFileWorker(QObject):
    history_loaded = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, history_file_path):
        super().__init__()
        self.history_file_path = history_file_path

    @pyqtSlot()
    def load_history(self):
        if not os.path.exists(self.history_file_path):
            self.history_loaded.emit([])
            return
        try:
            with open(self.history_file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            self.history_loaded.emit(history)
        except (json.JSONDecodeError, Exception) as e:
            self.error.emit(f"Erreur lors du chargement de l'historique: {e}")
            self.history_loaded.emit([])

    @pyqtSlot(list)
    def save_history(self, history_data):
        try:
            os.makedirs(os.path.dirname(self.history_file_path), exist_ok=True)
            with open(self.history_file_path, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=4)
        except Exception as e:
            self.error.emit(f"Erreur lors de la sauvegarde de l'historique: {e}")


class DummyDownloadRequest(QObject):
    stateChanged = pyqtSignal()

    def __init__(self, filename, path, parent=None):
        super().__init__(parent)
        self._filename = filename
        self._path = path
        self._state = QWebEngineDownloadRequest.DownloadState.DownloadCompleted

    def downloadFileName(self):
        return self._path

    def state(self):
        return self._state

    def receivedBytes(self):
        try:
            return os.path.getsize(self._path) if os.path.exists(self._path) else 0
        except OSError:
            return 0

    def totalBytes(self):
        return self.receivedBytes()

    def cancel(self):
        pass


class DownloadItemWidget(QFrame):
    delete_requested = pyqtSignal(QWidget)

    def __init__(self, download_item, parent=None):
        super().__init__(parent)
        self.download_item = download_item
        self.is_history_item = isinstance(download_item, DummyDownloadRequest)
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
        info_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Démarrage...")
        self.status_label.setObjectName("statusLabel")
        info_layout.addWidget(self.status_label)

        info_layout.addStretch(1)

        layout.addLayout(info_layout)
        layout.setStretch(1, 1)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("Button")
        self.cancel_button.clicked.connect(self.cancel_download)
        layout.addWidget(self.cancel_button)

        self.open_button = QPushButton("Ouvrir")
        self.open_button.setObjectName("Button")
        self.open_button.clicked.connect(self.open_file)
        layout.addWidget(self.open_button)

        self.delete_button = QPushButton("Supprimer")
        self.delete_button.setObjectName("Button")
        self.delete_button.clicked.connect(self.delete_item)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

        if not self.is_history_item:
            self.download_item.stateChanged.connect(self.update_state)
            self.download_item.receivedBytesChanged.connect(self.update_progress)

        self.update_state()

    def update_icon(self):
        style = self.style()
        icon = style.standardIcon(style.StandardPixmap.SP_FileIcon)
        self.icon_label.setPixmap(icon.pixmap(QSize(32, 32)))

    def sizeHint(self):
        return QSize(super().sizeHint().width(), 80)

    def update_state(self):
        state = self.download_item.state()

        is_in_progress = (
            state == QWebEngineDownloadRequest.DownloadState.DownloadInProgress
        )
        is_completed = (
            state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted
        )
        is_finished = state in [
            QWebEngineDownloadRequest.DownloadState.DownloadCompleted,
            QWebEngineDownloadRequest.DownloadState.DownloadCancelled,
            QWebEngineDownloadRequest.DownloadState.DownloadInterrupted,
        ]

        self.cancel_button.setVisible(is_in_progress)
        self.open_button.setVisible(is_completed)
        self.delete_button.setVisible(is_finished)

        if is_in_progress:
            self.progress_bar.show()
            self.status_label.show()
            self.update_progress()
        elif is_completed:
            self.progress_bar.hide()
            self.status_label.show()
            self.status_label.setText("Téléchargement terminé")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            self.progress_bar.hide()
            self.status_label.show()
            self.status_label.setText("Téléchargement annulé")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            self.progress_bar.hide()
            self.status_label.show()
            self.status_label.setText("Téléchargement interrompu")

        if self.is_history_item:
            self.progress_bar.hide()
            self.cancel_button.hide()
            self.open_button.show()
            self.delete_button.show()

        if is_finished and not self.is_history_item:
            try:
                self.download_item.stateChanged.disconnect(self.update_state)
                self.download_item.receivedBytesChanged.disconnect(self.update_progress)
            except TypeError:
                pass

    def update_progress(self):
        if (
            self.download_item.state()
            != QWebEngineDownloadRequest.DownloadState.DownloadInProgress
        ):
            return

        bytes_received = self.download_item.receivedBytes()
        bytes_total = self.download_item.totalBytes()

        received_mb = bytes_received / (1024 * 1024)

        if bytes_total > 0:
            total_mb = bytes_total / (1024 * 1024)
            percentage = int(bytes_received * 100 / bytes_total)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
            self.status_label.setText(
                f"Téléchargé {received_mb:.2f} Mo / {total_mb:.2f} Mo"
            )
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.status_label.setText(f"Téléchargé {received_mb:.2f} Mo")

    def cancel_download(self):
        self.progress_bar.hide()
        self.status_label.setText("Téléchargement annulé")
        self.cancel_button.hide()
        self.open_button.hide()
        self.delete_button.show()

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
        self.delete_requested.emit(self)


class DownloadManager(QWidget):
    DOWNLOAD_HISTORY_FILE = f"{directory}/resources/saves/download_history.json"
    request_save_history = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Téléchargements")
        self.setMinimumSize(500, 300)

        self.completed_downloads_history = []
        self.active_download_items = {}

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("downloadListWidget")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.list_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.apply_stylesheet()

        self.worker_thread = QThread()
        self.file_worker = DownloadFileWorker(self.DOWNLOAD_HISTORY_FILE)
        self.file_worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.file_worker.load_history)
        self.file_worker.history_loaded.connect(self.on_history_loaded)
        self.file_worker.error.connect(self.on_worker_error)
        self.request_save_history.connect(self.file_worker.save_history)

        self.worker_thread.start()

    def apply_stylesheet(self):
        try:
            css_path = os.path.abspath(f"{directory}/theme/theme.css")
            if os.path.exists(css_path):
                with open(css_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            else:
                print(f"Fichier CSS non trouvé : {css_path}")
        except Exception as e:
            print(f"Impossible de charger le thème pour DownloadManager: {e}")

    @pyqtSlot(QWebEngineDownloadRequest)
    def add_download(self, download_item: QWebEngineDownloadRequest):
        if download_item in self.active_download_items:
            return

        download_item.stateChanged.connect(
            lambda state, di=download_item: self.on_download_state_changed(state, di)
        )

        download_widget = DownloadItemWidget(download_item)
        download_widget.delete_requested.connect(self.remove_item_widget)
        self.active_download_items[download_item] = download_widget

        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(download_widget.sizeHint())
        self.list_widget.insertItem(0, list_item)
        self.list_widget.setItemWidget(list_item, download_widget)

        self.show()

    def on_download_state_changed(self, state, download_item):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
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
                    self.request_save_history.emit(self.completed_downloads_history)

        if state in [
            QWebEngineDownloadRequest.DownloadState.DownloadCompleted,
            QWebEngineDownloadRequest.DownloadState.DownloadCancelled,
            QWebEngineDownloadRequest.DownloadState.DownloadInterrupted,
        ]:
            if download_item in self.active_download_items:
                del self.active_download_items[download_item]

    @pyqtSlot(list)
    def on_history_loaded(self, history):
        self.completed_downloads_history = history
        for item_info in reversed(self.completed_downloads_history):
            dummy_item = DummyDownloadRequest(
                item_info["filename"], item_info["path"], self
            )

            widget = DownloadItemWidget(dummy_item)
            widget.delete_requested.connect(self.remove_item_widget)
            widget.status_label.setText(f"Terminé le {item_info['timestamp']}")

            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, widget)

    @pyqtSlot(QWidget)
    def remove_item_widget(self, widget_to_remove):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget is widget_to_remove:
                self.list_widget.takeItem(i)
                break

        if widget_to_remove.is_history_item:
            path_to_remove = widget_to_remove.download_item.downloadFileName()
            self.completed_downloads_history = [
                item
                for item in self.completed_downloads_history
                if item["path"] != path_to_remove
            ]
            self.request_save_history.emit(self.completed_downloads_history)

    @pyqtSlot(str)
    def on_worker_error(self, message):
        print(message)

    def closeEvent(self, event):
        self.worker_thread.quit()
        self.worker_thread.wait()
        super().closeEvent(event)
