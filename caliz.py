import sys
import serial

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray

SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE   = 9600


class PwmSerialPrinter(Node):

    def __init__(self):
        super().__init__("pwm_serial_printer")

        self.declare_parameter("serial_port", SERIAL_PORT)
        self.declare_parameter("baud_rate",   BAUD_RATE)

        port = self.get_parameter("serial_port").get_parameter_value().string_value
        baud = self.get_parameter("baud_rate").get_parameter_value().integer_value

        self.ser = serial.Serial(port, baud, timeout=1)
        self.get_logger().info(f"Serial abierto → {port} @ {baud}")

        self.create_subscription(
            Int16MultiArray,
            "pwm_values",
            self.pwm_callback,
            10
        )

    def pwm_callback(self, msg: Int16MultiArray):
        payload = str(msg.data[0])#";".join(str(v) for v in msg.data) + "\n"
        self.ser.write(payload.encode())
        print(payload)
        self.get_logger().debug(f"Serial enviado: {payload.strip()}")

    def __del__(self):
        if hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()


def main(args=None):
    rclpy.init(args=args)
    node = PwmSerialPrinter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        del node
        rclpy.shutdown()


if __name__ == "__main__":
    main(sys.argv)