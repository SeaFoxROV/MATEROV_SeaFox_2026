#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

import requests
import numpy as np



class CamerasPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')

        self.session = requests.Session()

        self.declare_parameter("main_cam_url", "http://admin:admin@192.168.1.9:6688/snapshot/PROFILE_000")
        self.declare_parameter("upper_cam_url", "http://admin:admin@192.168.1.4:6688/snapshot/PROFILE_000")
        self.declare_parameter("lower_cam_url", "http://admin:admin@192.168.1.4:6688/snapshot/PROFILE_000") #change when the third camera arrives

        self.bridge = CvBridge()

        self.cameras = {
            "main": {
                "url": self.get_parameter("main_cam_url").get_parameter_value().string_value,
                "pub": self.create_publisher(Image, "mainCamera", 10)
            },
            "upper": {
                "url": self.get_parameter("upper_cam_url").get_parameter_value().string_value,
                "pub": self.create_publisher(Image, "upperCamera", 10)
            },
            "lower": {
                "url": self.get_parameter("lower_cam_url").get_parameter_value().string_value,
                "pub": self.create_publisher(Image, "lowerCamera", 10)
            }
        }

        self.timer = self.create_timer(0.035, self.timer_callback)

    def timer_callback(self):

        for name, cam in self.cameras.items():
            try:
                r = self.session.get(cam["url"], timeout=0.07)
                img = cv2.imdecode(
                    np.frombuffer(r.content, np.uint8),
                    cv2.IMREAD_COLOR
                )

                if img is None:
                    continue

                msg = self.bridge.cv2_to_imgmsg(img, "bgr8")
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = name

                cam["pub"].publish(msg)

            except Exception as e:
                self.get_logger().warn(f"{name} cam error: {e}")

def main(args=None):
    rclpy.init(args=args)

    node = CamerasPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()