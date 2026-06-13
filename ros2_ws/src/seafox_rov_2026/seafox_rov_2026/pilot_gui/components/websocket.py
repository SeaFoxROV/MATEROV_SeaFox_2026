import json
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import Qt, QUrl, QByteArray
from PyQt5.QtNetwork import QAbstractSocket


class WebSocket:
    def __init__(self):
        self.ws_url = "ws://192.168.1.241:3001"
        self.ws_pending_message = None
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self._on_ws_connected)
        self.websocket.disconnected.connect(self._on_ws_disconnected)
        self.websocket.open(QUrl(self.ws_url))

    def _on_ws_connected(self):
        print(f"WebSocket conectado a {self.ws_url}")
        if self.ws_pending_message:
            self.websocket.sendBinaryMessage(self.ws_pending_message)
            print(f"Mensaje WebSocket enviado: {self.ws_pending_message}")
            self.ws_pending_message = None

    def _on_ws_disconnected(self):
        print("WebSocket desconectado")

    def _send_ws_message(self, image, annotated_results):
        print(":v")
        json_bytes = json.dumps(annotated_results).encode("utf-8")
        json_length = len(json_bytes)

        # Header: 4 bytes big-endian con el tamaño del JSON
        header = json_length.to_bytes(4, byteorder="big")

        # Empaquetar: header + json + imagen
        payload = header + json_bytes + bytes(image)
        print("CCC")
        self.websocket.sendBinaryMessage(QByteArray(payload))
        print(f"Mensaje WebSocket enviado: {len(payload)}")

        # elif self.websocket.state() == QAbstractSocket.ConnectingState:
        #     self.ws_pending_message = image
        #     print(f"WebSocket aún conectando a {self.ws_url}...")
        #     return
        #
        # self.ws_pending_message = message
        # print(f"Conectando WebSocket a {self.ws_url}...")
        # self.websocket.open(QUrl(self.ws_url))

    def _on_ws_error(self, error):
        print("WebSocket error:", self.websocket.errorString())

    def _on_ws_message(self, message):
        print("Mensaje recibido:", message)
