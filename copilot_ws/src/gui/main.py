from components.crabVision import crabVision
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtCore import QUrl, QObject, pyqtSignal


from components.photogrammetry import Photogrammetry
from components.iceberg import Iceberg
from components.eDNA import eDNA
from components.detection import Detection
from lib.websocket import WebsocketClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.photogrammetry = Photogrammetry()
        self.websocket = WebsocketClient()
        self.detection = Detection()

        self.setWindowTitle("Mi Template PyQt5")
        self.resize(900, 600)

        self.tabs = QTabWidget()

        self.tabs.addTab(self.photogrammetry, "Photogrammetry")
        self.tabs.addTab(Iceberg(), "Iceberg")
        self.tabs.addTab(self.detection, "Crab Vision")
        self.tabs.addTab(eDNA(), "eDNA")

        self.setCentralWidget(self.tabs)

        self.websocket.message_received.connect(self.photogrammetry._on_ws_message)
        self.websocket.message_received.connect(self.detection._on_ws_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
