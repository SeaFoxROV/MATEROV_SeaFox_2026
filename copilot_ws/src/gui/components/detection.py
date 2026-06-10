from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket
from PyQt5.QtGui import QImage, QPixmap

from lib.detectionManager import DetectionManager

import cv2
import numpy as np


class Detection(QWidget):
    def __init__(self):
        super().__init__()

        self.detection_manager = DetectionManager()
        self._image_size = None
        self._base_pixmap = None
        self.annotated_results = None
        # Qt variables
        layout = QVBoxLayout()
        self.message = None
        self.label = QLabel(f"Mensaje recibido: {self.message}")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(640, 480)
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.label.setMouseTracking(True)

        self.label.mousePressEvent = self._on_mouse_press
        self.label.mouseMoveEvent = self._on_mouse_move
        self.label.mouseReleaseEvent = self._on_mouse_release

    def _on_ws_message(self, image, annotated_results):
        self.set_image(image)
        self.annotated_results = annotated_results
        self.detection_manager.load(annotated_results)
        self._redraw()
        print(self.annotated_results)

    def set_image(self, image):
        cv_img = np.frombuffer(image, dtype=np.uint8)
        cv_img = cv2.imdecode(cv_img, cv2.IMREAD_COLOR)
        if cv_img is not None:
            height, width, channel = cv_img.shape
            bytes_per_line = 3 * width
            # to Qt
            q_img = QImage(
                cv_img.data, width, height, bytes_per_line, QImage.Format_RGB888
            ).rgbSwapped()
            # label signal
            pixmap = QPixmap.fromImage(q_img).scaled(
                self.label.width(),
                self.label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.label.setPixmap(pixmap)

            self._image_size = (cv_img.shape[1], cv_img.shape[0])  # (width, height)
            self._base_pixmap = pixmap  # guarda el pixmap limpio (sin anotaciones)

    def _on_mouse_press(self, event):
        if self._image_size is None:
            return
        changed = self.detection_manager.on_mouse_press(
            event,
            (self.label.width(), self.label.height()),
            self._image_size,
        )
        self._redraw()

    def _on_mouse_move(self, event):
        if self._image_size is None:
            return
        self.detection_manager.on_mouse_move(
            event,
            (self.label.width(), self.label.height()),
            self._image_size,
        )
        self._redraw()  # actualiza el recuadro en progreso

    def _on_mouse_release(self, event):
        if self._image_size is None:
            return
        self.detection_manager.on_mouse_release(
            event,
            (self.label.width(), self.label.height()),
            self._image_size,
        )
        self._redraw()

    def _redraw(self):
        if self._base_pixmap and self._image_size:
            annotated = self.detection_manager.draw_on_pixmap(
                self._base_pixmap, self._image_size
            )
            self.label.setPixmap(annotated)
