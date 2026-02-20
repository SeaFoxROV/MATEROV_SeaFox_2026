import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QHBoxLayout
from PyQt5.QtCore import Qt

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

    def keyPressEvent(self, event):
        if event.text() == 'B':
            self.left_widget.adjuster.set_brightness(self.left_widget.adjuster.brightness + 10)
        elif event.text() == 'b':
            self.left_widget.adjuster.set_brightness(self.left_widget.adjuster.brightness - 10)
        elif event.text() == 'C':
            self.left_widget.adjuster.set_contrast(self.left_widget.adjuster.contrast + 0.1)
        elif event.text() == 'c':
            self.left_widget.adjuster.set_contrast(self.left_widget.adjuster.contrast - 0.1)
        elif event.text() == 'S':
            self.left_widget.adjuster.set_saturation(self.left_widget.adjuster.saturation + 0.1)
        elif event.text() == 's':
            self.left_widget.adjuster.set_saturation(self.left_widget.adjuster.saturation - 0.1)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
