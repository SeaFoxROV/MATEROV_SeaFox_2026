import cv2
from ultralytics import YOLO
import os
 
 
class CrabDetector:
    def __init__(self):
        base_path  = os.path.dirname(__file__)
        model_path = os.path.join(base_path, "best.pt")
        self.model = YOLO(model_path)
 
    def detect(self, frame):

        results = self.model(frame, conf=0.6, iou=0.5, verbose=False)
 
        boxes = [
            box.xyxy[0].cpu().numpy().astype(int).tolist()
            for box in results[0].boxes
        ]
        count = len(boxes)
 
        return frame, boxes, count
 


 