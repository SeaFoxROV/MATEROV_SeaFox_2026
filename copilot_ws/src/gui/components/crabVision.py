import cv2
import numpy as np
from pathlib import Path
import traceback

try:
    from ultralytics import YOLO


except Exception as e:
    YOLO_AVAILABLE = False

    print("=" * 80)
    print("ERROR IMPORTANDO YOLO")
    print(type(e))
    print(e)
    traceback.print_exc()
    print("=" * 80)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap


class crabVision(QWidget):

    # ── hilo de detección (clase interna) ──────────────────────────────────
    class _DetectionThread(QThread):
        frame_ready = pyqtSignal(np.ndarray, int)
        finished_sig = pyqtSignal()

        def __init__(self, model, source, conf=0.6):
            super().__init__()
            self.model = model
            self.source = source
            self.conf = conf
            self._running = True

        def run(self):
            cap = cv2.VideoCapture(self.source)
            while self._running and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                results = self.model(frame, conf=self.conf,
                                     iou=0.5, verbose=False)
                count = len(results[0].boxes)
                annotated = results[0].plot()
                self.frame_ready.emit(annotated, count)
            cap.release()
            self.finished_sig.emit()

        def stop(self):
            self._running = False
            self.wait()

    # ── constructor principal ───────────────────────────────────────────────
    WEIGHTS = Path(__file__).parent / \
        "runs/detect/train/weights/best.pt"

    def __init__(self):
        super().__init__()
        self.model = None
        self.thread = None
        self._build_ui()
        self._load_model()

    # ── interfaz ───────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Video display
        self.display = QLabel("Abre un video o conecta la webcam")
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setMinimumHeight(400)
        self.display.setStyleSheet(
            "background:#111; color:#888; font-size:14px;")
        layout.addWidget(self.display, stretch=1)

        # Contador
        self.lbl_count = QLabel("Cangrejos: —")
        self.lbl_count.setAlignment(Qt.AlignCenter)
        self.lbl_count.setStyleSheet("font-size:22px; font-weight:bold;")
        layout.addWidget(self.lbl_count)

        # Controles
        row = QHBoxLayout()

        self.btn_video = QPushButton("Abrir video")
        self.btn_webcam = QPushButton("Webcam")
        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setEnabled(False)

        self.btn_video.clicked.connect(self._open_video)
        self.btn_webcam.clicked.connect(self._open_webcam)
        self.btn_stop.clicked.connect(self._stop)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 99)
        self.slider.setValue(60)
        self.slider.setFixedWidth(120)
        self.lbl_conf_val = QLabel("0.60")
        self.slider.valueChanged.connect(
            lambda v: self.lbl_conf_val.setText(f"{v/100:.2f}")
        )

        self.lbl_status = QLabel("Modelo cargando…")

        row.addWidget(self.btn_video)
        row.addWidget(self.btn_webcam)
        row.addWidget(self.btn_stop)
        row.addSpacing(20)
        row.addWidget(QLabel("Confianza:"))
        row.addWidget(self.slider)
        row.addWidget(self.lbl_conf_val)
        row.addStretch()
        row.addWidget(self.lbl_status)

        layout.addLayout(row)
        self.setLayout(layout)

    # ── modelo ─────────────────────────────────────────────────────────────
    def _load_model(self):
        try:
            self.model = YOLO(str(self.WEIGHTS))
            self.lbl_status.setText("Modelo listo ✓")

        except Exception as e:
            print(e)
            self.lbl_status.setText("Error al cargar modelo")
            self.display.setText(str(e))

    # ── acciones ───────────────────────────────────────────────────────────

    def _open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar video", "",
            "Videos (*.mp4 *.avi *.mov *.mkv)"
        )
        if path:
            self._launch(path)

    def _open_webcam(self):
        self._launch(0)

    def _launch(self, source):
        self._stop()
        self.btn_stop.setEnabled(True)
        self.btn_video.setEnabled(False)
        self.btn_webcam.setEnabled(False)

        conf = self.slider.value() / 100.0
        self.thread = self._DetectionThread(self.model, source, conf=conf)
        self.thread.frame_ready.connect(self._on_frame)
        self.thread.finished_sig.connect(self._on_finished)
        self.thread.start()

    def _stop(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
        self.thread = None
        self.btn_stop.setEnabled(False)
        self.btn_video.setEnabled(True)
        self.btn_webcam.setEnabled(True)

    # ── slots ──────────────────────────────────────────────────────────────
    def _on_frame(self, bgr, count):
        self.lbl_count.setText(f"Cangrejos: {count}")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        img = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            self.display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.display.setPixmap(pix)

    def _on_finished(self):
        self._stop()
        self.lbl_count.setText("Reproducción terminada")

    def closeEvent(self, event):
        self._stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = crabVision()
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec_())
