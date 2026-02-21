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
        self.all_cameras = False

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
        # Camera selection
        if event.text() == '1':
            self.left_widget.select_camera("main")
            self.all_cameras = False
            self.left_widget.set_title_style("main", "font-weight: bold; color: white; background-color: #2BCF47;")
        elif event.text() == '2':
            self.left_widget.select_camera("upper")
            self.all_cameras = False
            self.left_widget.set_title_style("upper", "font-weight: bold; color: white; background-color: #2BCF47;")
        elif event.text() == '3':
            self.left_widget.select_camera("middle")
            self.all_cameras = False
            self.left_widget.set_title_style("middle", "font-weight: bold; color: white; background-color: #2BCF47;")
        elif event.text() == '0':
            self.all_cameras = True
            for name in self.left_widget.threads.keys():
                self.left_widget.set_title_style(name, "font-weight: bold; color: white; background-color: #333;")

        # Quick conf
        elif event.text() == 'B':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_brightness(adjuster.brightness + 10)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_brightness(adjuster.brightness + 10)
        elif event.text() == 'b':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_brightness(adjuster.brightness - 10)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_brightness(adjuster.brightness - 10)
        elif event.text() == 'C':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_contrast(adjuster.contrast + 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_contrast(adjuster.contrast + 0.1)
        elif event.text() == 'c':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_contrast(adjuster.contrast - 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_contrast(adjuster.contrast - 0.1)
        elif event.text() == 'S':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_saturation(adjuster.saturation + 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_saturation(adjuster.saturation + 0.1)
        elif event.text() == 's':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_saturation(adjuster.saturation - 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_saturation(adjuster.saturation - 0.1)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
