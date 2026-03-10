from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket

class Photogrammetry(QWidget):
    def __init__(self):
        super().__init__()

        self.ws_url = "ws://192.168.1.95:3001"
        self.ws_pending_message = None
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self._on_ws_connected)
        self.websocket.disconnected.connect(self._on_ws_disconnected)
        self.websocket.textMessageReceived.connect(self._on_ws_message_received)
        self.message = None

        print(f"Conectando WebSocket a {self.ws_url}...")
        self.websocket.open(QUrl(self.ws_url))

        layout = QVBoxLayout()
        self.label = QLabel(f"Mensaje recibido: {self.message}")
        layout.addWidget(self.label)

        self.setLayout(layout)

    def _on_ws_connected(self):
        print(f"WebSocket conectado a {self.ws_url}")
        if self.ws_pending_message:
            self.websocket.sendTextMessage(self.ws_pending_message)
            print(f"Mensaje WebSocket enviado: {self.ws_pending_message}")
            self.ws_pending_message = None

    def _on_ws_disconnected(self):
        print("WebSocket desconectado")
    
    def _on_ws_message_received(self, message):
        print(f"Mensaje WebSocket recibido: {message}")
        self.message = message
        self.label.setText(f"Mensaje recibido: {self.message}")

    # def _send_ws_message(self, message):
    #     if self.websocket.state() == QAbstractSocket.ConnectedState:
    #         self.websocket.sendTextMessage(message)
    #         print(f"Mensaje WebSocket enviado: {message}")
    #         return

    #     self.ws_pending_message = message
    #     print(f"Conectando WebSocket a {self.ws_url}...")
    #     self.websocket.open(QUrl(self.ws_url))