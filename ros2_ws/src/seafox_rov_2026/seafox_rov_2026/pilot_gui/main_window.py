import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QHBoxLayout

from components.camera import CameraWidget
from components.model import ModelWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt5 - División Vertical")
        self.setGeometry(100, 100, 800, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        self.left_widget = CameraWidget()
        self.right_widget = ModelWidget()

        layout.addWidget(self.left_widget)
        layout.addWidget(self.right_widget)

        layout.setStretch(0, 1)
        layout.setStretch(1, 1)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
