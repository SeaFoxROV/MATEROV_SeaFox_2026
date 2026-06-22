from lib.imageManager import imageManager
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


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

        self.realHeightLabel = QDoubleSpinBox()
        self.realHeightLabel.setRange(0, 100000)
        self.realHeightLabel.setDecimals(2)
        self.realHeightLabel.setSingleStep(1)
        # Cuando está en 0 (vacío) muestra un texto guía en vez de "0.00"
        self.realHeightLabel.setSpecialValueText("Alto real")

        self.realWidthLabel = QDoubleSpinBox()
        self.realWidthLabel.setRange(0, 100000)
        self.realWidthLabel.setDecimals(2)
        self.realWidthLabel.setSingleStep(1)
        self.realWidthLabel.setSpecialValueText("Ancho real")

        # ── Ajuste manual para margen de error ──────────────────────────
        # Dos cajas independientes (una por Ancho, otra por Alto) + un
        # checkbox para "ligarlas" y que se muevan juntas con el mismo valor.
        self.widthAdjustmentTitle = QLabel("Ajuste Ancho (+/-)")
        self.widthAdjustmentBox = QDoubleSpinBox()
        self.widthAdjustmentBox.setRange(-1000, 1000)
        self.widthAdjustmentBox.setDecimals(2)
        self.widthAdjustmentBox.setSingleStep(1)
        self.widthAdjustmentBox.setValue(0)

        self.heightAdjustmentTitle = QLabel("Ajuste Alto (+/-)")
        self.heightAdjustmentBox = QDoubleSpinBox()
        self.heightAdjustmentBox.setRange(-1000, 1000)
        self.heightAdjustmentBox.setDecimals(2)
        self.heightAdjustmentBox.setSingleStep(1)
        self.heightAdjustmentBox.setValue(0)

        self.linkAdjustmentsCheckbox = QCheckBox(
            "Aplicar el mismo ajuste a Ancho y Alto (mover las dos al mismo tiempo)"
        )
        self.linkAdjustmentsCheckbox.stateChanged.connect(
            self._on_link_adjustments_toggled)

        self.calculateBtn = QPushButton("Calcular")
        self.calculateBtn.clicked.connect(self.calculate)

        layout.addWidget(self.widthLabel)
        layout.addWidget(self.heightLabel)
        layout.addWidget(self.realHeightLabel)
        layout.addWidget(self.realWidthLabel)

        layout.addWidget(self.widthAdjustmentTitle)
        layout.addWidget(self.widthAdjustmentBox)
        layout.addWidget(self.heightAdjustmentTitle)
        layout.addWidget(self.heightAdjustmentBox)
        layout.addWidget(self.linkAdjustmentsCheckbox)

        layout.addWidget(self.calculateBtn)

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

    def _on_link_adjustments_toggled(self, state):
        linked = state == Qt.Checked
        self.heightAdjustmentBox.setEnabled(not linked)

        if linked:

            self.heightAdjustmentBox.setValue(self.widthAdjustmentBox.value())
            self.widthAdjustmentBox.valueChanged.connect(
                self._sync_height_adjustment)
        else:
            try:
                self.widthAdjustmentBox.valueChanged.disconnect(
                    self._sync_height_adjustment)
            except TypeError:

                pass

    def _sync_height_adjustment(self, value):
        self.heightAdjustmentBox.setValue(value)

    def calculate(self):
        if self.widthLabelText is None or self.heightLabelText is None:
            print("Faltan puntos de ancho o alto en píxeles")
            return

        realWidth = self.realWidthLabel.value()
        realHeight = self.realHeightLabel.value()

        if realWidth > 0 and realHeight > 0:
            print("Llena solo uno de los dos campos")
            return

        if realWidth == 0 and realHeight == 0:
            print("Llena al menos un campo")
            return

        try:
            if realWidth:
                # Conozco el ancho real → calculo el alto real.
                adjustment = self.heightAdjustmentBox.value()

                result = (
                    float(realWidth) * float(self.heightLabelText)
                ) / float(self.widthLabelText)

                result += adjustment

                self.realHeightLabel.setValue(round(result, 4))

                print(
                    f"Alto calculado: {round(result, 4)} "
                    f"(ajuste aplicado: {adjustment})"
                )

            else:
                # Conozco el alto real → calculo el ancho real.
                adjustment = self.widthAdjustmentBox.value()

                result = (
                    float(realHeight) * float(self.widthLabelText)
                ) / float(self.heightLabelText)

                result += adjustment

                self.realWidthLabel.setValue(round(result, 4))

                print(
                    f"Ancho calculado: {round(result, 4)} "
                    f"(ajuste aplicado: {adjustment})"
                )

        except ValueError:
            print("El valor ingresado no es un número válido")
