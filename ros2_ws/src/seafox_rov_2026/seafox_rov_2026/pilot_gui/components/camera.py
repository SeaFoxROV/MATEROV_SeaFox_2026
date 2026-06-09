import sys
import cv2
import json
import numpy as np
import requests
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QVBoxLayout,
    QLabel,
    QWidget,
    QSizePolicy,
)
 
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QLabel, QWidget
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
        self.name     = name
        self.url      = url
        self.adjuster = adjuster
 
        self._run_flag       = True
        self.apply_adjustments = False
        self.qimg            = None
        self.last_frame      = None   
 
        self.detecter    = CrabDetector()
        self.isDetecting = False
 
        self.session   = requests.Session()
        self.websocket = WebSocket()
 

 
    def run(self):
        while self._run_flag:
            try:
                response = self.session.get(self.url, timeout=0.6)
                if response.status_code == 200:
                    array  = np.frombuffer(response.content, dtype=np.uint8)
                    cv_img = cv2.imdecode(array, cv2.IMREAD_COLOR)
 
                    if cv_img is not None:
                        cv_img = self.adjuster.apply(cv_img)
                        self.last_frame = cv_img.copy() 
 
                        display = cv_img
 
                        if self.isDetecting:
                          
                            _, boxes, count = self.detecter.detect(cv_img)
                 
                            display = cv_img.copy()
                            for (x1, y1, x2, y2) in boxes:
                                cv2.rectangle(display, (x1, y1), (x2, y2),
                                              (0, 255, 120), 2)
                            cv2.putText(
                                display,
                                f"Crabs: {count}",
                                (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (0, 255, 120), 2
                            )
 
                        h, w, _ = display.shape
                        q_img = QImage(
                            display.data, w, h, w * 3, QImage.Format_RGB888
                        ).rgbSwapped()
 
                        self.change_pixmap_signal.emit(q_img)
                        self.qimg = q_img
 
            except Exception:
                self.msleep(100)
 

 
    def start_detection(self, name):
        if self.name == name:
            self.isDetecting = True
 
    def stop_detection(self):
        self.isDetecting = False
 
   
 
    def send_detection_snapshot(self, name):

        if self.name != name:
            return
        if self.last_frame is None:
            print("No frame available yet")
            return
 
        frame, boxes, count = self.detecter.detect(self.last_frame)
        print(f"Detection: {count} crabs — sending to Copilot")
 

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            print("Failed to encode frame")
            return
        jpeg_bytes = bytes(buf)
 
   
        payload_json = json.dumps({
            "type":  "crab_detection",
            "boxes": boxes,
            "count": count,
        }).encode("utf-8")
 

        json_len   = len(payload_json).to_bytes(4, "little")
        message    = json_len + payload_json + jpeg_bytes
 
        self.websocket._send_ws_message(bytes(message))
 

    def send_snapshot(self, name):
        if self.name != name:
            return
        qimg = self.qimg.scaled(320, 240, Qt.KeepAspectRatio,
                                 Qt.SmoothTransformation)
        buffer = QBuffer()
        buffer.open(QBuffer.WriteOnly)
        qimg.save(buffer, "JPEG", quality=85)
        image_bytes = buffer.data()
        buffer.close()
        self.websocket._send_ws_message(image_bytes)
 
    def stop(self):
        self._run_flag = False
        self.wait()
 
 

class CameraWidget(QFrame):
    def __init__(self):
        super().__init__()
 
        self.camera_configs = {
            "main":   "http://admin:admin@192.168.1.68:6688/snapshot/PROFILE_000",
            "upper":  "http://admin:admin@192.168.1.67:6688/snapshot/PROFILE_000",
            "middle": "http://admin:admin@192.168.1.69:6688/snapshot/PROFILE_000",
        }
        self.titles = {}
        self.threads = {}
        self.labels = {}
        self.camera_containers = {}
        self.titles   = {}
        self.threads  = {}
        self.labels   = {}
        self.selected_camera = None
 
        self.setFrameShape(QFrame.StyledPanel)
        main_layout = QVBoxLayout()
 
        for name, url in self.camera_configs.items():
            adjuster      = ImageAdjuster()
            camera_layout = QVBoxLayout()
            camera_layout.setContentsMargins(0, 0, 0, 0)

 
            title = QLabel(name.upper())
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet(
                "font-weight: bold; color: white; background-color: #333;"
            )
            title.setStyleSheet(
                "font-weight: bold; color: white; background-color: #333;")
            self.titles[name] = title
 
            image_label = QLabel("Conectando...")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setMinimumSize(1, 1)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            image_label.setStyleSheet(
                "background-color: black; border: 1px solid gray;"
            )
            image_label.setFixedSize(640, 480)
            image_label.setStyleSheet(
                "background-color: black; border: 1px solid gray;")
            self.labels[name] = image_label
 
            camera_layout.addWidget(title)
            camera_layout.addWidget(image_label)
            container.setLayout(camera_layout)

            main_layout.addWidget(container)
            self.camera_containers[name] = container

            main_layout.addLayout(camera_layout)
 
            thread = VideoThread(name, url, adjuster)
            thread.change_pixmap_signal.connect(
                lambda img, lbl=image_label: self.set_image(img, lbl))
            thread.start()
            self.threads[name] = thread
 
        self.setLayout(main_layout)
 
    def set_image(self, q_img, label):
        pixmap = QPixmap.fromImage(q_img).scaled(
            label.width(), label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        for name in self.titles.keys():
            self.titles[name].setStyleSheet(
                "font-weight: bold; color: white; background-color: #333;"
            )
        for name in self.titles:
            self.titles[name].setStyleSheet(
                "font-weight: bold; color: white; background-color: #333;")
        if camera_name in self.titles:
            self.titles[camera_name].setStyleSheet(style)
 
    def maximize_camera(self, camera_name):
        for name, container in self.camera_containers.items():
            if name == camera_name:
                container.show()
            else:
                container.hide()
 
    def reset_camera_view(self):
        for container in self.camera_containers.values():
            container.show()
 
 
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

 