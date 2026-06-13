import socket
import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

UDP_IP   = "0.0.0.0"
UDP_PORT = 8889

# Orden exacto que manda el ESP32 en sendData()
FIELDS = ["pressure", "temperature", "depth", "altitude",
          "accelX", "accelY", "accelZ",
          "gyroX",  "gyroY",  "gyroZ"]


class SensorUdpReceiver(Node):

    def __init__(self):
        super().__init__("sensor_udp_receiver")

        self.pub_imu = self.create_publisher(Float32MultiArray, "sensors/imu",   10)
        self.pub_bar = self.create_publisher(Float32MultiArray, "sensors/bar02", 10)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)
        self.create_timer(0.02, self.recv_udp)  # 50 Hz

        self.get_logger().info(f"Escuchando sensores UDP en {UDP_IP}:{UDP_PORT}")

    def parse_packet(self, payload: str) -> dict | None:
        parts = payload.strip().split(";")
        if len(parts) != len(FIELDS):
            return None
        try:
            return {field: float(val) for field, val in zip(FIELDS, parts)}
        except ValueError:
            return None

    def recv_udp(self):
        try:
            data, addr = self.sock.recvfrom(256)
        except BlockingIOError:
            return

        sensors = self.parse_packet(data.decode())  # fix: sin print()
        if sensors is None:
            self.get_logger().warn(f"Paquete inválido de {addr}: {data}")
            return

        # --- Bar02: [pressure, temperature, depth, altitude] ---
        bar_msg = Float32MultiArray()
        bar_msg.data = [
            sensors["pressure"], sensors["temperature"],
            sensors["depth"],    sensors["altitude"],
        ]
        self.pub_bar.publish(bar_msg)

        # --- IMU: [accelX, accelY, accelZ, gyroX, gyroY, gyroZ] ---
        imu_msg = Float32MultiArray()
        imu_msg.data = [
            sensors["accelX"], sensors["accelY"], sensors["accelZ"],
            sensors["gyroX"],  sensors["gyroY"],  sensors["gyroZ"],
        ]
        self.pub_imu.publish(imu_msg)

        self.get_logger().debug(
            f"[{addr[0]}] P={sensors['pressure']:.2f}mbar "
            f"D={sensors['depth']:.2f}m "
            f"accel=({sensors['accelX']:.3f}, {sensors['accelY']:.3f}, {sensors['accelZ']:.3f})"
        )

    def __del__(self):
        self.sock.close()


def main(args=None):
    rclpy.init(args=args)
    node = SensorUdpReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        del node
        rclpy.shutdown()


if __name__ == "__main__":
    main(sys.argv)