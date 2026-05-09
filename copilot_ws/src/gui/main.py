import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

from components.crabVision import crabVision
from components.eDNA import eDNA
from components.iceberg import Iceberg
from components.photogrammetry import Photogrammetry

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mi Template PyQt5")
        self.resize(900, 600)

        self.tabs = QTabWidget()

        self.tabs.addTab(Photogrammetry(), "Photogrammetry")
        self.tabs.addTab(Iceberg(), "Iceberg")
        self.tabs.addTab(crabVision(), "Crab Vision")
        self.tabs.addTab(eDNA(), "eDNA")

        self.setCentralWidget(self.tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


    