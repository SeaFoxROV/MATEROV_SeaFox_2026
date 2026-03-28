from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
from lib.imageManager import imageManager


class Photogrammetry(QWidget):
    def __init__(self):
        super().__init__()

        self.ws_url = "ws://10.4.68.201:3001"
        self.ws_pending_message = None
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self._on_ws_connected)
        self.websocket.disconnected.connect(self._on_ws_disconnected)
        self.websocket.binaryMessageReceived.connect(self._on_ws_message)
        self.message = None

        print(f"Conectando WebSocket a {self.ws_url}...")
        self.websocket.open(QUrl(self.ws_url))

        layout = QVBoxLayout()
        self.label = QLabel(f"Mensaje recibido: {self.message}")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(640, 480)
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.image_manager = imageManager()
        self.points = []

        self.label.setMouseTracking(True)
        self.label.mousePressEvent = self._on_mouse_press

    def _on_ws_connected(self):
        print(f"WebSocket conectado a {self.ws_url}")
        if self.ws_pending_message:
            self.websocket.sendBinaryMessage(self.ws_pending_message)
            print(f"Mensaje WebSocket enviado: {self.ws_pending_message}")
            self.ws_pending_message = None

    def _on_ws_disconnected(self):
        print("WebSocket desconectado")

    def _on_ws_message(self, message):
        self.set_image(message)
        print(f"Mensaje WebSocket recibido: {message}")

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
            self.image_manager.set_image(q_img)

    def _on_mouse_press(self, event):
        if self.image_manager.image is None:
            return

        pos = event.pos()
        self.points.append((pos.x(), pos.y()))
        print(f"Coordenada seleccionada: {pos.x()}, {pos.y()}")

        if len(self.points) == 2:
            p1, p2 = self.points
            distance = self.image_manager.pixel_distance(self.label, p1, p2)

            if distance is not None:
                print(f"Distancia entre puntos: {distance:.2f} píxeles")

        self.points = []

    # def _send_ws_message(self, message):
    #     if self.websocket.state() == QAbstractSocket.ConnectedState:
    #         self.websocket.sendBinaryMessage(message)
    #         print(f"Mensaje WebSocket enviado: {message}")
    #         return

    #     self.ws_pending_message = message
    #     print(f"Conectando WebSocket a {self.ws_url}...")
    #     self.websocket.open(QUrl(self.ws_url))

