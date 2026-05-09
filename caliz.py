#!/usr/bin/env python3
import sys
import threading

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer


class ImageSub(Node):
    def __init__(self, topic="/mainCamera"):
        super().__init__("mainCameraSub")
        self.bridge = CvBridge()
        self.frame = None

        self.create_subscription(
            Image,
            topic,
            self.cb,
            10
        )

        print(f"Subscribed to {topic}")

    def cb(self, msg):
        self.frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")


def ros_spin(node):
    rclpy.spin(node)


def main():
    rclpy.init()

    node = ImageSub("/mainCamera")

    t = threading.Thread(target=ros_spin, args=(node,), daemon=True)
    t.start()

    app = QApplication(sys.argv)
    label = QLabel("Waiting for image...")
    label.setScaledContents(True)
    label.resize(640, 480)

    def update():
        if node.frame is None:
            return

        rgb = cv2.cvtColor(node.frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(img))

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(10)  # ~30 FPS

    label.show()
    app.exec_()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
