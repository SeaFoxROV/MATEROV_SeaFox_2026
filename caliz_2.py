import asyncio
import websockets
import json
import cv2
import numpy as np

async def test():
    uri = "ws://127.0.0.1:3001"  # hacer pruebas des la pc
    
    
    img = cv2.imread("test.png")
    if img is None:
        img = np.zeros((480, 640, 3), dtype="uint8")

    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    jpeg_bytes = bytes(buf)

    payload = json.dumps({
        "type": "crab_detection",
        "boxes": [[50, 40, 180, 140], [220, 60, 370, 190]],
        "count": 2,
    }).encode("utf-8")

    json_len = len(payload).to_bytes(4, "little")
    message = json_len + payload + jpeg_bytes

    async with websockets.connect(uri) as ws:
        await ws.send(message)
        print("Mensaje enviado OK")

asyncio.run(test())