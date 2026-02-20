import sys
import cv2
import numpy as np
import requests
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from .camera_quick_config import ImageAdjuster

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, url, adjuster):
        super().__init__()
        self.url = url
        self._run_flag = True
        self.adjuster = adjuster
        self.session = requests.Session()

    def run(self):
        while self._run_flag:
            try:
                # snapshot
                response = self.session.get(self.url, timeout=0.6)
                if response.status_code == 200:
                    array = np.frombuffer(response.content, dtype=np.uint8)
                    cv_img = cv2.imdecode(array, cv2.IMREAD_COLOR)

                    if cv_img is not None:
                        cv_img = self.adjuster.apply(cv_img)
                        height, width, channel = cv_img.shape
                        bytes_per_line = 3 * width
                        # to Qt
                        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                        # label signal
                        self.change_pixmap_signal.emit(q_img)
            except Exception as e:
                self.msleep(100)

    def stop(self):
        self._run_flag = False
        self.wait()

class CameraWidget(QFrame):
    def __init__(self):
        super().__init__()
        
        self.camera_configs = {
            "main": "http://admin:admin@192.168.1.68:6688/snapshot/PROFILE_000",
            # "upper": "http://admin:admin@192.168.1.9:6688/snapshot/PROFILE_000",
            # "middle": "http://admin:admin@192.168.1.4:6688/snapshot/PROFILE_000",
        }
        self.adjuster = ImageAdjuster()

        self.threads = []
        self.setFrameShape(QFrame.StyledPanel)
        main_layout = QVBoxLayout()

        for name, url in self.camera_configs.items():
            camera_layout = QVBoxLayout()

            title = QLabel(name.upper())
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("font-weight: bold; color: white; background-color: #333;")

            image_label = QLabel("Conectando...")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setFixedSize(640, 480)
            image_label.setStyleSheet("background-color: black; border: 1px solid gray;")

            camera_layout.addWidget(title)
            camera_layout.addWidget(image_label)
            main_layout.addLayout(camera_layout)

            thread = VideoThread(url, self.adjuster)
            thread.change_pixmap_signal.connect(
                lambda img, lbl=image_label: self.set_image(img, lbl)
            )
            thread.start()
            self.threads.append(thread)

        self.setLayout(main_layout)

    def set_image(self, q_img, label):
        pixmap = QPixmap.fromImage(q_img).scaled(
            label.width(), label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        label.setPixmap(pixmap)

    def closeEvent(self, event):
        for thread in self.threads:
            thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    win_layout = QVBoxLayout()
    
    cam_widget = CameraWidget()
    win_layout.addWidget(cam_widget)
    
    window.setLayout(win_layout)
    window.setWindowTitle("SeaFox ROV - Multi-Camera System")
    window.show()
    sys.exit(app.exec_())