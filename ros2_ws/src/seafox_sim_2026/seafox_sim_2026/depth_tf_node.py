import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from std_msgs.msg import Float32


class DepthTFNode(Node):

    def __init__(self):
        super().__init__('depth_tf_node')

        self.br = TransformBroadcaster(self)

        self.create_subscription(
            Float32,
            '/depth',
            self.depth_callback,
            10
        )

        self.timer = self.create_timer(0.05, self.publish_tf)

        self.depth = 0.0  # valor inicial

    def depth_callback(self, msg):
        self.depth = msg.data

    def publish_tf(self):

        t = TransformStamped()

        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "world"
        t.child_frame_id = "base_link"   # 🔥 CAMBIADO AQUÍ

        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = self.depth

        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0

        self.br.sendTransform(t)


def main():
    rclpy.init()
    node = DepthTFNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()