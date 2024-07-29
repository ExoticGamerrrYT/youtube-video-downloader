from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QLabel,
    QComboBox,
)
from PySide6.QtCore import QThread, Signal, QSettings
from downloader import download_youtube_video, get_video_qualities, install_ffmpeg


class DownloadThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, url, path, quality):
        super().__init__()
        self.url = url
        self.path = path
        self.quality = quality

    def run(self):
        download_youtube_video(self.url, self.path, self.quality, self.log_signal.emit)
        self.finished_signal.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter YouTube URL")
        self.url_input.textChanged.connect(self.update_qualities)

        self.quality_dropdown = QComboBox(self)
        self.quality_dropdown.setEnabled(False)  # Disabled initially

        self.path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("Select download path")
        self.path_layout.addWidget(self.path_input)
        self.browse_button = QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.browse)
        self.path_layout.addWidget(self.browse_button)

        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.download)

        self.log_label = QLabel("Log", self)
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)

        layout.addWidget(self.url_input)
        layout.addWidget(self.quality_dropdown)
        layout.addLayout(self.path_layout)
        layout.addWidget(self.download_button)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

        self.loadSettings()

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.path_input.setText(path)

    def download(self):
        url = self.url_input.text()
        path = self.path_input.text()
        quality = self.quality_dropdown.currentText()
        if not url or not path or not quality:
            self.log_output.append(
                "Please enter a URL, select a path, and choose a quality."
            )
            return

        self.download_thread = DownloadThread(url, path, quality)
        self.download_thread.log_signal.connect(self.update_log)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.start()

        # Disable widgets during download
        self.url_input.setEnabled(False)
        self.path_input.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.quality_dropdown.setEnabled(False)

    def update_log(self, message):
        self.log_output.append(message)

    def download_finished(self):
        # Re-enable widgets after download
        self.url_input.setEnabled(True)
        self.path_input.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.quality_dropdown.setEnabled(True)

    def update_qualities(self):
        url = self.url_input.text()
        if url:
            qualities = get_video_qualities(url)
            self.quality_dropdown.clear()
            self.quality_dropdown.addItems(qualities)
            self.quality_dropdown.setEnabled(True)
        else:
            self.quality_dropdown.setEnabled(False)

    def loadSettings(self):
        """
        Loads the previously saved settings from QSettings.
        """
        settings = QSettings("Exotic Dev", "YouTube Downloader")
        self.path_input.setText(settings.value("savePath", ""))

    def saveSettings(self):
        """
        Saves the current settings to QSettings.
        """
        settings = QSettings("Exotic Dev", "YouTube Downloader")
        settings.setValue("savePath", self.path_input.text())

    def closeEvent(self, event):
        """
        Handles the close event to save the settings before the application closes.
        """
        self.saveSettings()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
