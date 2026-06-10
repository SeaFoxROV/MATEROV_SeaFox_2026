from components.crabVision import crabVision
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtWebSockets import QWebSocketServer
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtCore import QByteArray
import json

from components.photogrammetry import Photogrammetry
from components.iceberg import Iceberg
from components.eDNA import eDNA


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mi Template PyQt5")
        self.resize(900, 600)

        self.tabs = QTabWidget()

        self.tabs.addTab(Photogrammetry(), "Photogrammetry")
        self.tabs.addTab(Iceberg(), "Iceberg")

        self.crab_tab = crabVision()                     
        self.tabs.addTab(self.crab_tab, "Crab Vision")

        self.tabs.addTab(eDNA(), "eDNA")

        self.setCentralWidget(self.tabs)

        # Servidor WebSocket
        self.clients = []
        self.ws_server = QWebSocketServer("CopilotServer",
                                          QWebSocketServer.NonSecureMode)
        if self.ws_server.listen(QHostAddress.Any, 3001):
            print("WS server escuchando en puerto 3001")
        else:
            print("ERROR: no se pudo abrir el puerto 3001")
        self.ws_server.newConnection.connect(self._on_new_connection)

    def _on_new_connection(self):
        client = self.ws_server.nextPendingConnection()
        client.binaryMessageReceived.connect(self._on_binary_message)
        client.disconnected.connect(lambda: self.clients.remove(client))  # limpiar lista
        self.clients.append(client)
        print(f"Pilot conectado: {client.peerAddress().toString()}")

    def _on_binary_message(self, data: QByteArray):
        try:
            raw = bytes(data)
            json_len = int.from_bytes(raw[:4], "little")
            payload = json.loads(raw[4:4 + json_len])
            jpeg_bytes = raw[4 + json_len:]

            self.crab_tab.receive_detection({     
                "image": bytes(jpeg_bytes),
                "boxes": payload.get("boxes", [])
            })

            # Cambiar al tab de Crab Vision automaticamente
            self.tabs.setCurrentWidget(self.crab_tab)

        except Exception as e:
            print(f"Error parseando mensaje WS: {e}")

    def closeEvent(self, event):
        self.ws_server.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()