from email.mime import message
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QHBoxLayout
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtNetwork import QAbstractSocket

from components.camera import CameraWidget
from components.model import ModelWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt5 - División Vertical")
        self.setGeometry(100, 100, 800, 500)
        self.all_cameras = False
        self.selected_camera = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        self.left_widget = CameraWidget()
        self.right_widget = ModelWidget()

        layout.addWidget(self.left_widget)
        layout.addWidget(self.right_widget)

        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        self.ws_url = "ws://10.4.73.49:3001"
        self.ws_pending_message = None
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self._on_ws_connected)
        self.websocket.disconnected.connect(self._on_ws_disconnected)

    def _on_ws_connected(self):
        print(f"WebSocket conectado a {self.ws_url}")
        if self.ws_pending_message:
            self.websocket.sendBinaryMessage(self.ws_pending_message)
            print(f"Mensaje WebSocket enviado: {self.ws_pending_message}")
            self.ws_pending_message = None

    def _on_ws_disconnected(self):
        print("WebSocket desconectado")

    def _send_ws_message(self, message):
        if self.websocket.state() == QAbstractSocket.ConnectedState:
            self.websocket.sendBinaryMessage(message)
            print(f"Mensaje WebSocket enviado: {message}")
            return

        elif self.websocket.state() == QAbstractSocket.ConnectingState:
            self.ws_pending_message = message
            print(f"WebSocket aún conectando a {self.ws_url}...")
            return

        self.ws_pending_message = message
        print(f"Conectando WebSocket a {self.ws_url}...")
        self.websocket.open(QUrl(self.ws_url))

    def _on_ws_error(self, error):
        print("WebSocket error:", self.websocket.errorString())

    def _on_ws_message(self, message):
        print("Mensaje recibido:", message)

    def keyPressEvent(self, event):
        # Camera selection
        if event.text() == '1':
            if self.selected_camera == "1":
                self.left_widget.maximize_camera("main")
            self.selected_camera = "1"
            self.left_widget.select_camera("main")
            self.all_cameras = False
            self.left_widget.set_title_style("main", "font-weight: bold; color: white; background-color: #2BCF47;")
        elif event.text() == '2':
            if self.selected_camera == "2":
                self.left_widget.maximize_camera("upper")
            self.selected_camera = "2"
            self.left_widget.select_camera("upper")
            self.all_cameras = False
            self.left_widget.set_title_style("upper", "font-weight: bold; color: white; background-color: #2BCF47;")
        elif event.text() == '3':
            if self.selected_camera == "3":
                self.left_widget.maximize_camera("middle")
            self.selected_camera = "3"
            self.left_widget.select_camera("middle")
            self.all_cameras = False
            self.left_widget.set_title_style("middle", "font-weight: bold; color: white; background-color: #2BCF47;")
        elif event.text() == '0':
            self.selected_camera = 0
            self.all_cameras = True
            for name in self.left_widget.threads.keys():
                self.left_widget.set_title_style(name, "font-weight: bold; color: white; background-color: #333;")
        elif event.key() == Qt.Key_Escape:
            self.left_widget.reset_camera_view()

        # WebSocket conf
        elif event.key() == Qt.Key_Space:
            self._send_ws_message(self.left_widget.get_snapshot())

        # Quick conf
        elif event.text() == 'B':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_brightness(adjuster.brightness + 10)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_brightness(adjuster.brightness + 10)
        elif event.text() == 'b':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_brightness(adjuster.brightness - 10)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_brightness(adjuster.brightness - 10)
        elif event.text() == 'C':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_contrast(adjuster.contrast + 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_contrast(adjuster.contrast + 0.1)
        elif event.text() == 'c':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_contrast(adjuster.contrast - 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_contrast(adjuster.contrast - 0.1)
        elif event.text() == 'S':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_saturation(adjuster.saturation + 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_saturation(adjuster.saturation + 0.1)
        elif event.text() == 's':
            if self.all_cameras:
                for name in self.left_widget.threads.keys():
                    adjuster = self.left_widget.threads[name].adjuster
                    adjuster.set_saturation(adjuster.saturation - 0.1)
            else:
                adjuster = self.left_widget.get_selected_camera()
                if adjuster:
                    adjuster.set_saturation(adjuster.saturation - 0.1)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
