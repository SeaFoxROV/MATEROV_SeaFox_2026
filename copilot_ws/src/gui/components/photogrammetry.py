from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lib.imageManager import imageManager
# TODO: Poner en varios modulos el EDNA, Websocket y la fotogramtetria
# TODO: Tambien implementar la seleccion y deseleccion de imagenes basado en el diccionario de annotated_results


class Photogrammetry(QWidget):
    def __init__(self):
        super().__init__()

        self.ws_url = "ws://10.4.83.70:3001"
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

        self.widthLabelText = None
        self.heightLabelText = None
        self.realWidthLabelText = None
        self.realHeightLabelText = None

        self.mode = 1  # impar para ancho par para alto

        self.widthLabel = QLabel(f"Ancho: {self.widthLabelText}")
        self.heightLabel = QLabel(f"Alto: {self.heightLabelText}")

        self.realHeightLabel = QLineEdit()
        self.realHeightLabel.setPlaceholderText("Alto real")

        self.realWidthLabel = QLineEdit()
        self.realWidthLabel.setPlaceholderText("Ancho real")

        self.calculateBtn = QPushButton("Calcular")
        self.calculateBtn.clicked.connect(self.calculate)

        self.annotated_results = None

        layout.addWidget(self.widthLabel)
        layout.addWidget(self.heightLabel)
        layout.addWidget(self.realHeightLabel)
        layout.addWidget(self.realWidthLabel)
        layout.addWidget(self.calculateBtn)

    def _on_ws_connected(self):
        print(f"WebSocket conectado a {self.ws_url}")
        if self.ws_pending_message:
            self.websocket.sendBinaryMessage(self.ws_pending_message)
            print(f"Mensaje WebSocket enviado: {self.ws_pending_message}")
            self.ws_pending_message = None

    def _on_ws_disconnected(self):
        print("WebSocket desconectado")

    def _on_ws_message(self, image, annotated_results):
        self.set_image(image)
        self.annotated_results = annotated_results
        print(f"Mensaje WebSocket recibido: {image}")

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
        print(len(self.points))
        if len(self.points) == 2:
            p1, p2 = self.points
            distance = self.image_manager.pixel_distance(self.label, p1, p2)

            if self.mode % 2 == 1:
                self.setWidth(distance)
            else:
                self.setHeight(distance)

            self.points = []
            self.mode += 1

    def setWidth(self, width):
        self.widthLabelText = width
        self.widthLabel.setText(f"Ancho: {self.widthLabelText}")
        print(f"Ancho establecido: {self.widthLabelText}")

    def setHeight(self, height):
        self.heightLabelText = height
        self.heightLabel.setText(f"Alto: {self.heightLabelText}")
        print(f"Alto establecido: {self.heightLabelText}")

    def calculate(self):
        if not self.widthLabelText or not self.heightLabelText:
            print("Faltan puntos de ancho o alto en píxeles")
            return

        realWidth = self.realWidthLabel.text().strip()
        realHeight = self.realHeightLabel.text().strip()

        # Validar que solo uno esté lleno
        if realWidth and realHeight:
            print("Llena solo uno de los dos campos")
            return

        if not realWidth and not realHeight:
            print("Llena al menos un campo")
            return

        try:
            if realWidth:
                # Tengo ancho real → calculo alto real
                # alto_real / ancho_real = heightPx / widthPx
                result = (float(realWidth) * self.heightLabelText) / self.widthLabelText
                self.realHeightLabel.setText(str(round(result, 4)))

            else:
                # Tengo alto real → calculo ancho real
                result = (
                    float(realHeight) * self.widthLabelText
                ) / self.heightLabelText
                self.realWidthLabel.setText(str(round(result, 4)))

        except ValueError:
            print("El valor ingresado no es un número válido")
