import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from geometry_msgs.msg import Vector3Stamped


class CalizNode(Node):

    def __init__(self):
        super().__init__('caliz_node')

        # Publishers
        self.depth_pub = self.create_publisher(Float32, '/depth', 10)
        self.desired_pub = self.create_publisher(Vector3Stamped, '/desired_force', 10)
        self.perceived_pub = self.create_publisher(Vector3Stamped, '/perceived_force', 10)

        self.timer = self.create_timer(0.05, self.publish_signals)

        # Initial values
        self.depth = 1.0
        self.depth_direction = -1.0

        self.force_value = 1.0
        self.force_direction = -1.0

        self.perceived_value = -1.0
        self.perceived_direction = 1.0

        self.step = 0.02

    def publish_signals(self):

        # -----------------
        # DEPTH (1 → 0 → 1)
        # -----------------
        self.depth += self.step * self.depth_direction

        if self.depth <= 0.0:
            self.depth = 0.0
            self.depth_direction = 1.0

        if self.depth >= 1.0:
            self.depth = 1.0
            self.depth_direction = -1.0

        depth_msg = Float32()
        depth_msg.data = self.depth
        self.depth_pub.publish(depth_msg)

        # -----------------
        # DESIRED FORCE (1 → -1)
        # -----------------
        self.force_value += self.step * self.force_direction

        if self.force_value <= -1.0:
            self.force_value = -1.0
            self.force_direction = 1.0

        if self.force_value >= 1.0:
            self.force_value = 1.0
            self.force_direction = -1.0

        desired_msg = Vector3Stamped()
        desired_msg.header.stamp = self.get_clock().now().to_msg()
        desired_msg.header.frame_id = "base_link"

        desired_msg.vector.x = self.force_value
        desired_msg.vector.y = self.force_value
        desired_msg.vector.z = self.force_value

        self.desired_pub.publish(desired_msg)

        # -----------------
        # PERCEIVED FORCE (-1 → 1)
        # -----------------
        self.perceived_value += self.step * self.perceived_direction

        if self.perceived_value >= 1.0:
            self.perceived_value = 1.0
            self.perceived_direction = -1.0

        if self.perceived_value <= -1.0:
            self.perceived_value = -1.0
            self.perceived_direction = 1.0

        perceived_msg = Vector3Stamped()
        perceived_msg.header.stamp = self.get_clock().now().to_msg()
        perceived_msg.header.frame_id = "base_link"

        perceived_msg.vector.x = self.perceived_value
        perceived_msg.vector.y = self.perceived_value
        perceived_msg.vector.z = self.perceived_value

        self.perceived_pub.publish(perceived_msg)


def main():
    rclpy.init()
    node = CalizNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()