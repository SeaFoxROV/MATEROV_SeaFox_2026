import sys
import cv2
import numpy as np
import requests
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QBuffer
from PyQt5.QtGui import QImage, QPixmap
from lib.vision.crabDetection import CrabDetector
from components.websocket import WebSocket

from .camera_quick_config import ImageAdjuster
# TODO: Revisar como se va a comportar la camara con el resize en linux


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, name, url, adjuster):
        super().__init__()
        self.name = name
        self.url = url
        self._run_flag = True
        self.adjuster = adjuster
        self.session = requests.Session()
        self.apply_adjustments = False
        self.qimg = None

        self.detecter = CrabDetector()
        self.isDetecting = False

        self.websocket = WebSocket()
        self.annotated_results = None

    def run(self):
        while self._run_flag:
            try:
                # snapshot
                response = self.session.get(self.url, timeout=0.3)
                if response.status_code == 200:
                    array = np.frombuffer(response.content, dtype=np.uint8)
                    cv_img = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    # cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    if cv_img is not None:
                        cv_img = self.adjuster.apply(cv_img)
                        if self.isDetecting:
                            print("Haciendo deteccion")
                            self.annotated_results = self.detecter.detect(cv_img)
                        height, width, channel = cv_img.shape
                        bytes_per_line = 3 * width

                        # to Qt
                        q_img = QImage(
                            cv_img.data,
                            width,
                            height,
                            bytes_per_line,
                            QImage.Format_RGB888,
                        ).rgbSwapped()
                        # label signal
                        self.change_pixmap_signal.emit(q_img)
                        self.qimg = q_img
            except Exception as e:
                self.msleep(100)

    def start_detection(self, name):
        print(self.name)
        if self.name == name:
            # print("ENTRASTE")
            self.isDetecting = True

    def stop_detection(self):
        self.isDetecting = False

    def stop(self):
        self._run_flag = False
        self.wait()

    def send_snapshot(self, name):
        if self.name != name:
            return
        if self.qimg is None:
            return
        qimg = self.qimg.scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        buffer = QBuffer()
        buffer.open(QBuffer.WriteOnly)
        qimg.save(buffer, "JPEG", quality=85)  # o "PNG" si prefieres sin pérdida
        image_bytes = buffer.data()  # Esto es QByteArray
        buffer.close()

        detections = self.annotated_results or {}
        self.websocket._send_ws_message(image_bytes, detections)


class CameraWidget(QFrame):
    def __init__(self):
        super().__init__()

        self.camera_configs = {
            "main": "http://admin:admin@192.168.1.27:6688/snapshot/PROFILE_000",
            "upper": "http://admin:admin@192.168.1.67:6688/snapshot/PROFILE_000",
            "middle": "http://admin:admin@192.168.1.68:6688/snapshot/PROFILE_000",
        }
        self.titles = {}
        self.threads = {}
        self.labels = {}
        self.camera_containers = {}
        self.selected_camera = None
        self.maximized_camera = None  # ← rastrea cuál está maximizada
        self.setFrameShape(QFrame.StyledPanel)

        # Layout raíz
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Fila superior: 2 cámaras lado a lado
        top_row = QHBoxLayout()
        top_row.setSpacing(2)

        # Fila inferior: 1 cámara centrada
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(2)

        row_map = {
            "main": top_row,
            "upper": top_row,
            "middle": bottom_row,
        }

        for name, url in self.camera_configs.items():
            adjuster = ImageAdjuster()

            container = QWidget()
            camera_layout = QVBoxLayout(container)
            camera_layout.setContentsMargins(0, 0, 0, 0)
            camera_layout.setSpacing(0)

            title = QLabel(name.upper())
            title.setAlignment(Qt.AlignCenter)
            title.setFixedHeight(20)
            title.setStyleSheet(
                "font-weight: bold; color: white; background-color: #333;"
            )
            self.titles[name] = title

            image_label = QLabel("Conectando...")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setMinimumSize(1, 1)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            image_label.setStyleSheet(
                "background-color: black; border: 1px solid gray;"
            )
            self.labels[name] = image_label

            camera_layout.addWidget(title)
            camera_layout.addWidget(image_label)
            self.camera_containers[name] = container

            row_map[name].addWidget(container)

            thread = VideoThread(name, url, adjuster)
            thread.change_pixmap_signal.connect(
                lambda img, lbl=image_label: self.set_image(img, lbl)
            )
            thread.start()
            self.threads[name] = thread

        # Wrap rows en widgets para poder controlar show/hide por fila
        top_widget = QWidget()
        top_widget.setLayout(top_row)
        top_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_row)
        bottom_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(top_widget, stretch=1)
        main_layout.addWidget(bottom_widget, stretch=1)

        self.top_widget = top_widget
        self.bottom_widget = bottom_widget

    def set_image(self, q_img, label):
        pixmap = QPixmap.fromImage(q_img).scaled(
            label.width(),
            label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        label.setPixmap(pixmap)

    def closeEvent(self, event):
        for thread in self.threads.values():
            thread.stop()
        event.accept()

    def select_camera(self, camera_name):
        for thread in self.threads.values():
            thread.apply_adjustments = False
        if camera_name in self.threads:
            self.threads[camera_name].apply_adjustments = True
            self.selected_camera = camera_name

    def get_selected_camera(self):
        if self.selected_camera is None:
            return None
        return self.threads[self.selected_camera].adjuster

    def set_title_style(self, camera_name, style):
        for name, title in self.titles.items():
            title.setStyleSheet(
                "font-weight: bold; color: white; background-color: #333;"
            )
        if camera_name in self.titles:
            self.titles[camera_name].setStyleSheet(style)

    def maximize_camera(self, camera_name):
        if camera_name not in self.camera_containers:
            return
        self.maximized_camera = camera_name
        for name, container in self.camera_containers.items():
            container.setVisible(name == camera_name)
        # Muestra solo la fila que contiene la cámara, oculta la otra
        top_names = {"main", "upper"}
        if camera_name in top_names:
            self.top_widget.show()
            self.bottom_widget.hide()
        else:
            self.top_widget.hide()
            self.bottom_widget.show()

    def reset_camera_view(self):
        self.maximized_camera = None
        # Restaurar todos los contenedores
        for container in self.camera_containers.values():
            container.show()
        # Restaurar ambas filas
        self.top_widget.show()
        self.bottom_widget.show()


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
