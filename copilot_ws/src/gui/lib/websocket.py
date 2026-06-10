from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtCore import QUrl, QObject, pyqtSignal


class WebsocketClient(QObject):
    message_received = pyqtSignal(bytes, dict)

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

    def _on_ws_connected(self):
        print(f"WebSocket conectado a {self.ws_url}")
        if self.ws_pending_message:
            self.websocket.sendBinaryMessage(self.ws_pending_message)
            print(f"Mensaje WebSocket enviado: {self.ws_pending_message}")
            self.ws_pending_message = None

    def _on_ws_disconnected(self):
        print("WebSocket desconectado")

    def _on_ws_message(self, image, annotated_results):
        self.annotated_results = annotated_results
        self.message_received.emit(image, annotated_results)
        print(f"Mensaje WebSocket recibido: {image}")
