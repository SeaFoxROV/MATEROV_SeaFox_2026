from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QUrl
import math


class imageManager:
    def __init__(self):
        self.image = None
        self.pixelWidth = 0
        self.pixelHeight = 0
        self.width = 0
        self.height = 0

    def set_image(self, image):
        self.image = image

    def pointImage(self, label):
        if self.image is not None:
            pixmap = QPixmap.fromImage(self.image).scaled(
                label.width(),
                label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            label.setPixmap(pixmap)

    def labelCoords(self, label, x, y):
        if self.image is None:
            return None, None

        img_w = self.image.width()
        img_h = self.image.height()
        lbl_w = label.width()
        lbl_h = label.height()

        scale = min(lbl_w / img_w, lbl_h / img_h)
        scaled_w = img_w * scale
        scaled_h = img_h * scale

        offset_x = (lbl_w - img_w * scale) / 2
        offset_y = (lbl_h - img_h * scale) / 2

        if not (
            offset_x <= x <= offset_x + scaled_w
            and offset_y <= y <= offset_y + scaled_h
        ):
            return None, None

        img_x = (x - offset_x) / scale
        img_y = (y - offset_y) / scale
        return int(img_x), int(img_y)

    def pixel_distance(self, label, x1, x2):
        x1, y1 = self.labelCoords(label, *x1)
        x2, y2 = self.labelCoords(label, *x2)

        if x1 is None or x2 is None or y1 is None or y2 is None:
            return None

        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
