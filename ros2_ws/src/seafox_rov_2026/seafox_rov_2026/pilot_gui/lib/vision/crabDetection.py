import cv2
from ultralytics import YOLO
import os


class CrabDetector:
    def __init__(self):
        base_path = os.path.dirname(__file__)
        model_path = os.path.join(base_path, "best.pt")
        self.model = YOLO(model_path)

    def detect(self, frame):
        results = self.model(frame, conf=0.6)

        count = len(results[0].boxes)
        annotated = results[0].plot()
        h, w, _ = annotated.shape
        cv2.putText(
            annotated,
            f"Green Crabs Counter: {count}",
            (w - 250, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2,
        )

        return annotated, count
