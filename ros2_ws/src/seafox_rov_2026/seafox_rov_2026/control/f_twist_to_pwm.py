import rclpy
from rclpy.node import Node 

from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray, Int16MultiArray


class TwistToPWM(Node):

    def __init__(self):
        super().__init__("twist_to_pwm")

        # 6 thrusters + 2 extras (ej: gripper)
        self.pwm_setpoints = [1500] * 6
        self.pwm_values = [1500] * 8

        self.create_subscription(Twist, "/desired_twist", self.setpoint_callback, 10)
        self.create_subscription(Float32MultiArray, "/joystick_data", self.gripper_callback, 10)

        self.pwm_pub = self.create_publisher(Int16MultiArray, "pwm_values", 10)

        self.create_timer(0.1, self.pwm_callback)

    # ---------------- UTIL ----------------
    def normalize(self, val, scale=400):
        return int(val * scale)

    def clamp(self, val, min_v=1100, max_v=1900):
        return max(min(val, max_v), min_v)

    # ---------------- GRIPPER ----------------
    def gripper_callback(self, msg: Float32MultiArray):
        try:
            if msg.data[11]:
                self.pwm_values[6] = 1600
            elif msg.data[10]:
                self.pwm_values[6] = 1400
            else:
                self.pwm_values[6] = 1500
        except:
            pass

    # ---------------- MIXING ----------------
    def setpoint_callback(self, msg: Twist):

        # Normalización
        x = self.normalize(msg.linear.x)
        y = self.normalize(-msg.linear.y)
        z = self.normalize(msg.linear.z)

        roll  = self.normalize(msg.angular.x)
        pitch = self.normalize(msg.angular.y)  # no usado aún
        yaw   = self.normalize(msg.angular.z)

        base = 1500

        # Thruster mixing
        self.pwm_setpoints[0] = base + x + y - yaw       # M1
        self.pwm_setpoints[1] = base + z + roll          # M2
        self.pwm_setpoints[2] = base - x + y + yaw       # M3
        self.pwm_setpoints[3] = base + x - y + yaw       # M4
        self.pwm_setpoints[4] = base + z - roll          # M5
        self.pwm_setpoints[5] = base - x - y - yaw       # M6

        # Clamp
        for i in range(6):
            self.pwm_setpoints[i] = self.clamp(self.pwm_setpoints[i])

    # ---------------- OUTPUT ----------------
    def pwm_callback(self):

        # Combina setpoints + extras
        for i in range(6):
            self.pwm_values[i] = self.pwm_setpoints[i]

        msg = Int16MultiArray()
        msg.data = self.pwm_values

        self.pwm_pub.publish(msg)


# ---------------- MAIN ----------------
def main(args=None):
    rclpy.init(args=args)
    node = TwistToPWM()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()