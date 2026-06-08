
from __future__ import annotations
from typing import List, Dict, Optional
 
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QBrush, QFont,
)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Palette  (one place to change colours)
# ─────────────────────────────────────────────────────────────────────────────
 
_BG      = "#0f0f0f"   # canvas / window background
_SURFACE = "#161616"   # panel / card background
_BORDER  = "#242424"   # subtle borders
_TEXT    = "#e0e0e0"   # primary text
_MUTED   = "#555555"   # secondary / disabled text
_ACCENT  = "#e8e8e8"   # white-ish accent (count number, validate btn)
_BOX     = "#ffffff"   # normal box stroke (white, thin)
_SEL     = "#f0c040"   # selected box stroke (amber)
_NEW     = "#7090ff"   # rubber-band draw stroke (blue)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────────────────
 
class BoundingBox:
    _next_id: int = 1
 
    def __init__(self, x1: int, y1: int, x2: int, y2: int,
                 box_id: Optional[int] = None):
        if box_id is None:
            self.id = BoundingBox._next_id
            BoundingBox._next_id += 1
        else:
            self.id = box_id
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
 
    @property
    def width(self) -> int:
        return self.x2 - self.x1
 
    @property
    def height(self) -> int:
        return self.y2 - self.y1
 
    def as_dict(self) -> Dict:
        return {"id": self.id,
                "x1": self.x1, "y1": self.y1,
                "x2": self.x2, "y2": self.y2}
 
    def contains(self, x: int, y: int) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2
 
    def copy(self) -> "BoundingBox":
        return BoundingBox(self.x1, self.y1, self.x2, self.y2, self.id)
 
    @classmethod
    def from_xyxy(cls, coords: List[int]) -> "BoundingBox":
        return cls(*coords)
 
    @classmethod
    def reset_counter(cls):
        cls._next_id = 1
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Canvas
# ─────────────────────────────────────────────────────────────────────────────
 
_HANDLE = 6
 
class _Mode:
    NONE   = "none"
    DRAW   = "draw"
    MOVE   = "move"
    RESIZE = "resize"
 
 
class BoxCanvas(QLabel):
    boxes_changed = pyqtSignal()
    box_selected  = pyqtSignal(int)
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"background:{_BG};")
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
 
        self._pixmap:    Optional[QPixmap]    = None
        self._img_rect:  QRect                = QRect()
        self.boxes:      List[BoundingBox]    = []
        self._sel:       int                  = -1
        self._mode:      str                  = _Mode.NONE
        self._drag_start:    Optional[QPoint] = None
        self._drag_orig:     Optional[BoundingBox] = None
        self._resize_corner: Optional[str]    = None
        self._new_rect:      Optional[QRect]  = None
 
    # ── public ────────────────────────────────────────────────────────────
 
    def load_image(self, image):
        if isinstance(image, QPixmap):
            self._pixmap = image
        elif isinstance(image, QImage):
            self._pixmap = QPixmap.fromImage(image)
        elif isinstance(image, (bytes, bytearray)):
            pix = QPixmap()
            pix.loadFromData(image)
            self._pixmap = pix
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")
        self.update()
 
    def load_boxes(self, box_list: List[List[int]]):
        BoundingBox.reset_counter()
        self.boxes = [BoundingBox.from_xyxy(b) for b in box_list]
        self._sel = -1
        self.boxes_changed.emit()
        self.update()
 
    def clear(self):
        self._pixmap = None
        self.boxes   = []
        self._sel    = -1
        self.boxes_changed.emit()
        self.update()
 
    @property
    def selected_box(self) -> Optional[BoundingBox]:
        return next((b for b in self.boxes if b.id == self._sel), None)
 
    def delete_selected(self):
        if self._sel == -1:
            return
        self.boxes = [b for b in self.boxes if b.id != self._sel]
        self._sel  = -1
        self.boxes_changed.emit()
        self.box_selected.emit(-1)
        self.update()
 
    # ── paint ─────────────────────────────────────────────────────────────
 
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(_BG))
 
        if not self._pixmap:
            p.setPen(QColor(_MUTED))
            p.setFont(QFont("Helvetica Neue", 13))
            p.drawText(self.rect(), Qt.AlignCenter, "Waiting for detection data")
            p.end()
            return
 
        scaled = self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        ox = (self.width()  - scaled.width())  // 2
        oy = (self.height() - scaled.height()) // 2
        self._img_rect = QRect(ox, oy, scaled.width(), scaled.height())
        p.drawPixmap(ox, oy, scaled)
 
        for box in self.boxes:
            self._paint_box(p, box, box.id == self._sel)
 
        if self._new_rect and self._mode == _Mode.DRAW:
            p.setPen(QPen(QColor(_NEW), 1, Qt.DashLine))
            p.setBrush(QBrush(QColor(112, 144, 255, 20)))
            p.drawRect(self._new_rect)
 
        p.end()
 
    def _paint_box(self, p: QPainter, box: BoundingBox, selected: bool):
        wx1, wy1 = self._to_w(box.x1, box.y1)
        wx2, wy2 = self._to_w(box.x2, box.y2)
        rect = QRect(QPoint(wx1, wy1), QPoint(wx2, wy2))
 
        color = QColor(_SEL) if selected else QColor(_BOX)
 
        # Box outline — 1 px, no fill
        p.setPen(QPen(color, 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(rect)
 
        # ID label — small, muted
        p.setPen(QPen(color))
        p.setFont(QFont("Helvetica Neue", 9))
        p.drawText(wx1 + 3, wy1 - 3, f"{box.id}")
 
        if selected:
            # Corner handles — small filled squares
            hs = _HANDLE
            p.setBrush(QBrush(color))
            p.setPen(Qt.NoPen)
            for cx, cy in [(wx1, wy1), (wx2, wy1),
                           (wx1, wy2), (wx2, wy2)]:
                p.drawRect(cx - hs // 2, cy - hs // 2, hs, hs)
 
    # ── coord conversion ──────────────────────────────────────────────────
 
    def _to_w(self, ix: int, iy: int):
        if self._img_rect.isEmpty():
            return ix, iy
        sx = self._img_rect.width()  / (self._pixmap.width()  or 1)
        sy = self._img_rect.height() / (self._pixmap.height() or 1)
        return int(self._img_rect.x() + ix * sx), \
               int(self._img_rect.y() + iy * sy)
 
    def _to_i(self, wx: int, wy: int):
        if self._img_rect.isEmpty() or not self._pixmap:
            return wx, wy
        sx = self._pixmap.width()  / (self._img_rect.width()  or 1)
        sy = self._pixmap.height() / (self._img_rect.height() or 1)
        ix = max(0, min((wx - self._img_rect.x()) * sx, self._pixmap.width()))
        iy = max(0, min((wy - self._img_rect.y()) * sy, self._pixmap.height()))
        return int(ix), int(iy)
 
    def _in_img(self, wx: int, wy: int) -> bool:
        return self._img_rect.contains(QPoint(wx, wy))
 
    # ── hit testing ───────────────────────────────────────────────────────
 
    def _corner_at(self, wx: int, wy: int):
        if self._sel == -1 or not self.selected_box:
            return None
        box = self.selected_box
        for corner, (bx, by) in [
            ("tl", (box.x1, box.y1)), ("tr", (box.x2, box.y1)),
            ("bl", (box.x1, box.y2)), ("br", (box.x2, box.y2)),
        ]:
            cx, cy = self._to_w(bx, by)
            if abs(wx - cx) <= _HANDLE and abs(wy - cy) <= _HANDLE:
                return box, corner
        return None
 
    def _box_at(self, wx: int, wy: int) -> Optional[BoundingBox]:
        ix, iy = self._to_i(wx, wy)
        for box in reversed(self.boxes):
            if box.contains(ix, iy):
                return box
        return None
 
    # ── mouse ─────────────────────────────────────────────────────────────
 
    def mousePressEvent(self, e):
        if not self._pixmap:
            return
        wx, wy = e.x(), e.y()
        if e.button() == Qt.LeftButton:
            ch = self._corner_at(wx, wy)
            if ch:
                box, corner = ch
                self._mode = _Mode.RESIZE
                self._drag_start = QPoint(wx, wy)
                self._drag_orig  = box.copy()
                self._resize_corner = corner
                return
            hit = self._box_at(wx, wy)
            if hit:
                self._sel  = hit.id
                self._mode = _Mode.MOVE
                self._drag_start = QPoint(wx, wy)
                self._drag_orig  = hit.copy()
                self.box_selected.emit(hit.id)
                self.boxes_changed.emit()
                self.update()
                return
            if self._in_img(wx, wy):
                self._sel      = -1
                self._mode     = _Mode.DRAW
                self._drag_start = QPoint(wx, wy)
                self._new_rect   = QRect(wx, wy, 0, 0)
                self.box_selected.emit(-1)
                self.update()
        elif e.button() == Qt.RightButton:
            self._sel = -1
            self.box_selected.emit(-1)
            self.update()
 
    def mouseMoveEvent(self, e):
        wx, wy = e.x(), e.y()
        if self._mode == _Mode.NONE:
            if self._corner_at(wx, wy):
                self.setCursor(Qt.SizeFDiagCursor)
            elif self._box_at(wx, wy):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.CrossCursor)
 
        if self._mode == _Mode.DRAW and self._drag_start:
            x0, y0 = self._drag_start.x(), self._drag_start.y()
            self._new_rect = QRect(min(x0,wx), min(y0,wy),
                                   abs(wx-x0), abs(wy-y0))
            self.update()
 
        elif self._mode == _Mode.MOVE and self._drag_start and self._drag_orig:
            dw = wx - self._drag_start.x()
            dh = wy - self._drag_start.y()
            if not self._img_rect.isEmpty() and self._pixmap:
                sx = self._pixmap.width()  / (self._img_rect.width()  or 1)
                sy = self._pixmap.height() / (self._img_rect.height() or 1)
                di, dj = int(dw*sx), int(dh*sy)
            else:
                di, dj = dw, dh
            box = self.selected_box
            if box:
                o = self._drag_orig
                iw = self._pixmap.width()  if self._pixmap else 9999
                ih = self._pixmap.height() if self._pixmap else 9999
                nx1 = max(0, min(o.x1+di, iw-o.width))
                ny1 = max(0, min(o.y1+dj, ih-o.height))
                box.x1, box.y1 = nx1, ny1
                box.x2, box.y2 = nx1+o.width, ny1+o.height
                self.boxes_changed.emit()
                self.update()
 
        elif self._mode == _Mode.RESIZE and self._drag_start and self._drag_orig:
            dw = wx - self._drag_start.x()
            dh = wy - self._drag_start.y()
            if not self._img_rect.isEmpty() and self._pixmap:
                sx = self._pixmap.width()  / (self._img_rect.width()  or 1)
                sy = self._pixmap.height() / (self._img_rect.height() or 1)
                di, dj = int(dw*sx), int(dh*sy)
            else:
                di, dj = dw, dh
            box = self.selected_box
            if box:
                o = self._drag_orig
                x1, y1, x2, y2 = o.x1, o.y1, o.x2, o.y2
                c = self._resize_corner
                if "l" in c: x1 = min(x1+di, x2-4)
                if "r" in c: x2 = max(x2+di, x1+4)
                if "t" in c: y1 = min(y1+dj, y2-4)
                if "b" in c: y2 = max(y2+dj, y1+4)
                box.x1, box.y1, box.x2, box.y2 = x1, y1, x2, y2
                self.boxes_changed.emit()
                self.update()
 
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self._mode == _Mode.DRAW and self._new_rect:
                r = self._new_rect
                if r.width() > 6 and r.height() > 6:
                    ix1, iy1 = self._to_i(r.left(),  r.top())
                    ix2, iy2 = self._to_i(r.right(), r.bottom())
                    nb = BoundingBox(ix1, iy1, ix2, iy2)
                    self.boxes.append(nb)
                    self._sel = nb.id
                    self.box_selected.emit(nb.id)
                    self.boxes_changed.emit()
                self._new_rect = None
            self._mode = _Mode.NONE
            self._drag_start = self._drag_orig = self._resize_corner = None
            self.update()
 
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update()
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Right panel
# ─────────────────────────────────────────────────────────────────────────────
 
def _btn(label: str, color: str) -> QPushButton:
    b = QPushButton(label)
    b.setFixedHeight(32)
    b.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {color};
            border: 1px solid {color};
            border-radius: 3px;
            font-size: 11px;
            padding: 0 10px;
        }}
        QPushButton:hover {{
            background: {color};
            color: {_BG};
        }}
        QPushButton:disabled {{
            color: {_MUTED};
            border-color: {_BORDER};
        }}
    """)
    return b
 
 
def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{_MUTED}; font-size:10px; margin-top:8px;")
    return lbl
 
 
class CoordinatesPanel(QWidget):
    validate_requested = pyqtSignal()
    add_box_requested  = pyqtSignal()
    delete_requested   = pyqtSignal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self.setStyleSheet(f"background:{_SURFACE}; border-left:1px solid {_BORDER};")
        self._build()
 
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(4)
 
        # Count block
        self.lbl_count = QLabel("—")
        self.lbl_count.setStyleSheet(
            f"color:{_ACCENT}; font-size:48px; font-weight:300;")
        root.addWidget(self.lbl_count)
 
        self.lbl_note = QLabel("awaiting detection")
        self.lbl_note.setStyleSheet(f"color:{_MUTED}; font-size:11px;")
        root.addWidget(self.lbl_note)
 
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color:{_BORDER}; margin-top:8px; margin-bottom:4px;")
        root.addWidget(line)
 
        # Table
        root.addWidget(_label("detections"))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["id", "x1 y1", "x2 y2"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStyleSheet(
            f"QHeaderView::section {{ background:{_SURFACE}; color:{_MUTED};"
            f" font-size:10px; border:none; border-bottom:1px solid {_BORDER}; }}")
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {_SURFACE};
                color: {_TEXT};
                gridline-color: {_BORDER};
                font-size: 11px;
                border: none;
            }}
            QTableWidget::item:selected {{ background: {_BORDER}; }}
        """)
        self.table.setFixedHeight(160)
        root.addWidget(self.table)
 
        root.addStretch()
 
        # Buttons
        self.btn_del      = _btn("delete selected", "#c04040")
        self.btn_validate = _btn("validate", _ACCENT)
 
        self.btn_del.setEnabled(False)
        self.btn_validate.setEnabled(False)
 
        self.btn_del.clicked.connect(self.delete_requested)
        self.btn_validate.clicked.connect(self.validate_requested)
 
        root.addWidget(self.btn_del)
        root.addWidget(self.btn_validate)
 
    # ── update ────────────────────────────────────────────────────────────
 
    def update_boxes(self, boxes: List[BoundingBox], validated: bool):
        n = len(boxes)
        self.lbl_count.setText(str(n) if boxes else "—")
        if validated:
            self.lbl_note.setText(f"validated  ·  {n} crabs")
            self.lbl_note.setStyleSheet(f"color:{_ACCENT}; font-size:11px;")
        else:
            self.lbl_note.setText("pending validation" if boxes else "awaiting detection")
            self.lbl_note.setStyleSheet(f"color:{_MUTED}; font-size:11px;")
 
        self.table.setRowCount(0)
        for box in boxes:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(box.id)))
            self.table.setItem(r, 1, QTableWidgetItem(f"{box.x1} {box.y1}"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{box.x2} {box.y2}"))
 
    def set_has_data(self, has_data: bool):
        self.btn_validate.setEnabled(has_data)
 
    def set_box_selected(self, selected: bool):
        self.btn_del.setEnabled(selected)
 
    def highlight_row(self, box_id: int):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == box_id:
                self.table.selectRow(row)
                return
        self.table.clearSelection()
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Status bar
# ─────────────────────────────────────────────────────────────────────────────
 
class StatusBar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._base = (f"background:{_BG}; font-size:11px;"
                      f"padding:0 12px; border-top:1px solid {_BORDER};")
        self.setStyleSheet(self._base + f"color:{_MUTED};")
        self.setText("ready")
 
    def post(self, msg: str, level: str = "info"):
        c = {"info": _MUTED, "ok": _ACCENT, "warn": "#c08030", "err": "#c04040"
             }.get(level, _MUTED)
        self.setStyleSheet(self._base + f"color:{c};")
        self.setText(msg)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Main widget
# ─────────────────────────────────────────────────────────────────────────────
 
class crabVision(QWidget):
    """
    Copilot Crab Vision tab.
 
    Public API
    ----------
    receive_detection(payload: dict)
        {
            "image": QPixmap | QImage | bytes,
            "boxes": [[x1,y1,x2,y2], ...]
        }
 
    validated_result (signal) → dict
        { "count": int, "boxes": [{id,x1,y1,x2,y2}, …] }
    """
 
    validated_result = pyqtSignal(dict)
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._validated        = False
        self._pilot_box_count  = 0
        self._build_ui()
        self._connect()
 
    def _build_ui(self):
        self.setStyleSheet(f"background:{_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
 
        # ── top bar ──────────────────────────────────────────────────────
        bar = QWidget()
        bar.setFixedHeight(36)
        bar.setStyleSheet(f"background:{_SURFACE}; border-bottom:1px solid {_BORDER};")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(14, 0, 14, 0)
 
        title = QLabel("Crab Vision")
        title.setStyleSheet(f"color:{_TEXT}; font-size:12px;")
        bl.addWidget(title)
        bl.addStretch()
 
        self.lbl_source = QLabel("no data")
        self.lbl_source.setStyleSheet(f"color:{_MUTED}; font-size:11px;")
        bl.addWidget(self.lbl_source)
 
        root.addWidget(bar)
 
        # ── body ─────────────────────────────────────────────────────────
        split = QSplitter(Qt.Horizontal)
        split.setHandleWidth(1)
        split.setStyleSheet(f"QSplitter::handle {{ background:{_BORDER}; }}")
 
        self.canvas = BoxCanvas()
        split.addWidget(self.canvas)
 
        self.panel = CoordinatesPanel()
        split.addWidget(self.panel)
 
        split.setStretchFactor(0, 4)
        split.setStretchFactor(1, 1)
        root.addWidget(split, stretch=1)
 
        # ── status ───────────────────────────────────────────────────────
        self.status = StatusBar()
        root.addWidget(self.status)
 
    def _connect(self):
        self.canvas.boxes_changed.connect(self._on_changed)
        self.canvas.box_selected.connect(self._on_selected)
        self.panel.validate_requested.connect(self._on_validate)
        self.panel.delete_requested.connect(self.canvas.delete_selected)
 
    # ── public ────────────────────────────────────────────────────────────
 
    def receive_detection(self, payload: dict):
        image = payload.get("image")
        boxes = payload.get("boxes", [])
        self._validated       = False
        self._pilot_box_count = len(boxes)
        if image is not None:
            self.canvas.load_image(image)
        self.canvas.load_boxes(boxes)
        self.panel.set_has_data(True)
        self.panel.update_boxes(self.canvas.boxes, validated=False)
        self.lbl_source.setText(f"{self._pilot_box_count} boxes")
        self.status.post(
            f"received {self._pilot_box_count} detections — review and validate",
            "info")
 
    # ── slots ─────────────────────────────────────────────────────────────
 
    def _on_changed(self):
        self._validated = False
        self.panel.update_boxes(self.canvas.boxes, validated=False)
 
    def _on_selected(self, box_id: int):
        self.panel.set_box_selected(box_id != -1)
        self.panel.highlight_row(box_id)
 
    def _on_validate(self):
        boxes = self.canvas.boxes
        n     = len(boxes)
        diff  = n - self._pilot_box_count
        self._validated = True
        self.panel.update_boxes(boxes, validated=True)
        note = (f"  (+{diff})" if diff > 0 else f"  ({diff})" if diff < 0 else "")
        self.status.post(f"validated — {n} crabs{note}", "ok")
        self.validated_result.emit({
            "count": n,
            "boxes": [b.as_dict() for b in boxes],
        })
 
    def closeEvent(self, e):
        super().closeEvent(e)
 
 
# ─────────────────────────────────────────────────────────────────────────────
#  Test harness
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
 
    app = QApplication(sys.argv)
    win = crabVision()
    win.setWindowTitle("CrabVision — Copilot")
    win.resize(1100, 660)
    win.show()
 
    def _fake():
        from PyQt5.QtGui import QPainter
        pix = QPixmap(640, 480)
        pix.fill(QColor(18, 18, 18))
        p = QPainter(pix)
        p.fillRect(0, 0, 640, 240, QColor(12, 12, 12))
        p.end()
        win.receive_detection({
            "image": pix,
            "boxes": [[50,40,180,140],[220,60,370,190],
                      [410,200,560,330],[100,280,240,410]],
        })
        win.validated_result.connect(lambda r: print("result:", r))
 
    QTimer.singleShot(600, _fake)
    sys.exit(app.exec_())