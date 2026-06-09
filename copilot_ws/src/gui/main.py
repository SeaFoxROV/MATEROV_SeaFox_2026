from components.crabVision import crabVision
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

from components.crabVision import crabVision
from components.iceberg import Iceberg
from components.photogrammetry import Photogrammetry
from components.percentage_species import EDNA

from components.iceberg import Iceberg
from components.eDNA import eDNA


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Copilot GUI")
        self.resize(900, 600)

        self.tabs = QTabWidget()

        self.tabs.addTab(Photogrammetry(), "Photogrammetry")
        self.tabs.addTab(Iceberg(), "Iceberg")
        self.tabs.addTab(crabVision(), "Crab Vision")
        self.tabs.addTab(EDNA(), "eDNA")

        self.setCentralWidget(self.tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
