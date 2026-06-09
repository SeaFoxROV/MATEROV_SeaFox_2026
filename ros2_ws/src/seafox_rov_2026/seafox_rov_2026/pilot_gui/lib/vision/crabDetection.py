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
        boxes = results[0].boxes

        detections = {}
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = int(box.cls[0])
            label = self.model.names[cls]

            detections[i] = {
                "label": label,
                "confidence": round(conf, 2),
                "box": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
            }

        return detections
