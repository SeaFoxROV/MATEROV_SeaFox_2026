import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3Stamped, Point
from visualization_msgs.msg import Marker, MarkerArray


class ForceVisualizer(Node):

    def __init__(self):
        super().__init__('force_visualizer')

        self.marker_pub = self.create_publisher(
            MarkerArray,
            'force_markers',
            10
        )

        self.create_subscription(
            Vector3Stamped,
            '/desired_force',
            self.desired_callback,
            10
        )

        self.create_subscription(
            Vector3Stamped,
            '/perceived_force',
            self.perceived_callback,
            10
        )

        self.desired = None
        self.perceived = None

        self.scale = 1  # Escala visual de las fuerzas

    # -----------------------------
    # Callbacks
    # -----------------------------

    def desired_callback(self, msg):
        self.desired = msg.vector
        self.publish_all()

    def perceived_callback(self, msg):
        self.perceived = msg.vector
        self.publish_all()

    # -----------------------------
    # Publicación principal
    # -----------------------------

    def publish_all(self):

        if self.desired is None or self.perceived is None:
            return

        marker_array = MarkerArray()

        forces = [
            (self.desired, 0, (0.0, 1.0, 0.0), "desired"),
            (self.perceived, 3, (1.0, 0.0, 0.0), "perceived")
        ]

        for vector, base_id, color, namespace in forces:

            components = [
                (vector.x, 0.0, 0.0),  # X
                (0.0, vector.y, 0.0),  # Y
                (0.0, 0.0, vector.z)   # Z
            ]

            for i, (x, y, z) in enumerate(components):

                marker = Marker()

                marker.header.frame_id = "base_link"
                marker.header.stamp = self.get_clock().now().to_msg()

                marker.ns = namespace
                marker.id = base_id + i

                marker.type = Marker.ARROW
                marker.action = Marker.ADD

                marker.scale.x = 0.04  # grosor del cuerpo
                marker.scale.y = 0.08  # grosor de la punta
                marker.scale.z = 0.08

                marker.color.r = color[0]
                marker.color.g = color[1]
                marker.color.b = color[2]
                marker.color.a = 1.0

                marker.lifetime.sec = 0

                start = Point()
                start.x = 0.0
                start.y = 0.0
                start.z = 0.0

                end = Point()
                end.x = x * self.scale
                end.y = y * self.scale
                end.z = z * self.scale

                marker.points = [start, end]

                marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)


def main():
    rclpy.init()
    node = ForceVisualizer()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()