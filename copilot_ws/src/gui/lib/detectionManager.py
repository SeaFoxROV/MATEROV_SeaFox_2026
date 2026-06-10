from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt5.QtCore import Qt, QRect


class DetectionManager:
    """
    Gestiona detecciones de bounding boxes en coordenadas de imagen original.
    """

    COLOR_AUTO = QColor(0, 255, 0)  # verde  → detecciones YOLO
    COLOR_DRAW = QColor(0, 200, 255)  # cyan   → en progreso

    def __init__(self):
        self.detections: dict = {}
        self._next_id: int = 0
        # estado del drag
        self._drawing: bool = False
        self._drag_start = None  # (ix, iy) en coords de imagen
        self._drag_current = None

    # ── Datos ──────────────────────────────────────────────────────────────

    def load(self, detections_dict: dict):
        """Reemplaza detecciones con el dict que viene del CrabDetector."""
        self.detections = {int(k): dict(v) for k, v in detections_dict.items()}
        self._next_id = (max(self.detections.keys()) + 1) if self.detections else 0

    def count(self) -> int:
        return len(self.detections)

    def add(self, x1, y1, x2, y2, label="european_green_crab", confidence=1.0) -> int:
        """Agrega una detección manual. Regresa el id asignado, o -1 si es muy pequeña."""
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return -1
        det_id = self._next_id
        self._next_id += 1
        self.detections[det_id] = {
            "label": label,
            "confidence": confidence,
            "box": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
        }
        return det_id

    def remove_at(self, img_x: float, img_y: float) -> bool:
        """Borra la detección que contenga el punto. Regresa True si borró algo."""
        for det_id in reversed(list(self.detections.keys())):
            b = self.detections[det_id]["box"]
            if b["x1"] <= img_x <= b["x2"] and b["y1"] <= img_y <= b["y2"]:
                del self.detections[det_id]
                return True
        return False

    def get_at(self, img_x: float, img_y: float) -> dict | None:
        """Regresa la detección bajo el cursor, sin borrarla."""
        for det_id in reversed(list(self.detections.keys())):
            b = self.detections[det_id]["box"]
            if b["x1"] <= img_x <= b["x2"] and b["y1"] <= img_y <= b["y2"]:
                return {"id": det_id, **self.detections[det_id]}
        return None

    def clear(self):
        self.detections.clear()
        self._next_id = 0

    def export(self) -> dict:
        """Regresa una copia del dict (para mandarlo por WebSocket, etc.)."""
        return {k: dict(v) for k, v in self.detections.items()}

    # ── Dibujo ─────────────────────────────────────────────────────────────

    def draw_on_pixmap(self, base_pixmap: QPixmap, image_size: tuple) -> QPixmap:
        """
        Dibuja todas las detecciones sobre una COPIA de base_pixmap.
        image_size: (width, height) de la imagen ORIGINAL (antes de escalar).
        Regresa el QPixmap anotado.
        """
        result = base_pixmap.copy()
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)

        iw, ih = image_size
        pw, ph = result.width(), result.height()
        scale = min(pw / iw, ph / ih)
        ox = (pw - iw * scale) / 2  # offset por letterbox
        oy = (ph - ih * scale) / 2

        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)

        for det in self.detections.values():
            b = det["box"]
            color = self.COLOR_AUTO if det["label"] == "manual" else self.COLOR_AUTO

            lx1 = int(b["x1"] * scale + ox)
            ly1 = int(b["y1"] * scale + oy)
            lx2 = int(b["x2"] * scale + ox)
            ly2 = int(b["y2"] * scale + oy)

            # recuadro
            painter.setPen(QPen(color, 2))
            painter.drawRect(lx1, ly1, lx2 - lx1, ly2 - ly1)

            # etiqueta con fondo
            text = f"{det['label']} {det['confidence']}"
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(text)
            th = fm.height()
            bg = QRect(lx1, ly1 - th - 4, tw + 6, th + 4)
            painter.fillRect(bg, color)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(lx1 + 3, ly1 - 4, text)

        # recuadro en progreso (drag)
        if self._drawing and self._drag_start and self._drag_current:
            sx = int(self._drag_start[0] * scale + ox)
            sy = int(self._drag_start[1] * scale + oy)
            cx = int(self._drag_current[0] * scale + ox)
            cy = int(self._drag_current[1] * scale + oy)
            painter.setPen(QPen(self.COLOR_DRAW, 2, Qt.DashLine))
            painter.drawRect(min(sx, cx), min(sy, cy), abs(cx - sx), abs(cy - sy))

        painter.end()
        return result

    # ── Coordenadas ────────────────────────────────────────────────────────

    def _label_to_image(self, lx, ly, label_size, image_size):
        lw, lh = label_size
        iw, ih = image_size
        scale = min(lw / iw, lh / ih)
        ox = (lw - iw * scale) / 2
        oy = (lh - ih * scale) / 2
        return (lx - ox) / scale, (ly - oy) / scale

    # ── Eventos de mouse (llama desde Photogrammetry) ──────────────────────

    def on_mouse_press(self, event, label_size, image_size) -> bool:
        """
        Llama desde mousePressEvent del label.
        Click izquierdo → inicia drag. Click derecho → borra detección.
        Regresa True si algo cambió.
        """
        ix, iy = self._label_to_image(
            event.pos().x(), event.pos().y(), label_size, image_size
        )
        if event.button() == Qt.RightButton:
            return self.remove_at(ix, iy)

        if event.button() == Qt.LeftButton:
            self._drawing = True
            self._drag_start = (ix, iy)
            self._drag_current = (ix, iy)

        return False

    def on_mouse_move(self, event, label_size, image_size):
        """Llama desde mouseMoveEvent del label."""
        if not self._drawing:
            return
        ix, iy = self._label_to_image(
            event.pos().x(), event.pos().y(), label_size, image_size
        )
        self._drag_current = (ix, iy)

    def on_mouse_release(self, event, label_size, image_size) -> int:
        """
        Llama desde mouseReleaseEvent del label.
        Regresa el id de la nueva detección, o -1 si no se creó.
        """
        if not self._drawing:
            return -1
        self._drawing = False
        start, current = self._drag_start, self._drag_current
        self._drag_start = self._drag_current = None
        if start and current:
            return self.add(start[0], start[1], current[0], current[1])
        return -1
