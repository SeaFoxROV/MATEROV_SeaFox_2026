import cv2
from ultralytics import YOLO

model = YOLO("best.pt")

class CrabDetector():
    def __init__(self):
        self.model = YOLO("best.pt")
# tamano de la ventana en compu
detector_name = "Green European Crab Counter Detecter"
cv2.namedWindow(detector_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(detector_name, 1000, 700)

# Camara que se usa
cap = cv2.VideoCapture(0)

# Resolucion de la camara
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# seteings del video de salida
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter("crab_detection.mp4", fourcc, 64.0, (1280, 720))

while True:

    ret, frame = cap.read()
    if not ret:
        print("Camara not detected")

    results = model(frame, conf=0.6)

    count = len(results[0].boxes)

    annotated = results[0].plot()

    cv2.putText(
        annotated,
        f"Green Crabs Counter: {count}",
        (480, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        .8,
        (255, 255, 0),
        2
    )

    out.write(annotated)

    cv2.imshow(detector_name, annotated)

    # presionar boton de "esc" para salir
    if cv2.waitKey(1) == 27:
        break

cap.release()
out.release()
cv2.destroyAllWindows()