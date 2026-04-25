MAX_FWD_THRUST = 36.3826715 * 2 # N
MAX_REV_THRUST = -28.6354180 * 2 # N

TOTAL_CURRENT_LIMIT = 70 # A
ESC_CURRENT_LIMIT = 40 # A

import sys

import rclpy

from rclpy.node import Node 

from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray

import numpy as np

from os import path

PATH = path.dirname(__file__)

class twist_to_newtons(Node):
    """
    Class that implements the kinematics.
    """

    def __init__(self):
        super().__init__("twist_to_newtons")

        self.motor_positions = [ # [X, Y, Z] Posiciones de los motores respecto al centro del ROV
            [-0.136 ,  0.1687, 0.048], # Motor 1
            [ 0.136,  0.1687, 0.048], # Motor 2
            [ 0.1406, -0.0010, 0.031], # Motor 3
            [-0.1406, -0.0010, 0.031], # Motor 4
            [ 0.1896, -0.1270,-0.061], # Motor 5
            [-0.1896, -0.1270,-0.061]  # Motor 6
           
        ]
        
        self.motor_thrusts = [ # [X, Y, Z] Fuerzas descompuestas respecto a la orientacion del ROV
            [ -0.7071,  -0.7071, 0.0],   # Motor 1
            [0.7071,  -0.7071, 0.0],   # Motor 2 
            [    0.0,     0.0, 1.0],   # Motor 3
            [0.0, 0.0, 1.0],  # Motor 3
            [0.0, 0.0, 1.0],  # Motor 4
            [0.7071,  -0.7071, 0.0],   # Motor 6
            
        ]

        self.center_of_mass = [0.0,0.0,0.0] #[X,Y,Z] Posicion del centro de masa respecto al centro del ROV 

        self.motor_config = self.generate_motor_config(self.center_of_mass)

        self.inverse_config = np.linalg.pinv(self.motor_config, rcond=1e-15, hermitian=False)

        
        self.thrust_pub = self.create_publisher(Float32MultiArray, "motor_values", 10)
        self.subscription = self.create_subscription(Twist, "desired_twist", self.thrust_callback, 10)


    def generate_motor_config(self, center_of_mass_offset):
        """
        Generate the motor configuration matrix based on motor positions and thrust. Allows for
        a shifting center of mass, so the motor configuration can be regenerated dynamically to
        account for center of mass shifts when lifting objects.

        Returns:
            Motor configuration matrix based on motor orientation, position, and location of center of mass
        """
        shifted_positons = [(np.subtract(motor, center_of_mass_offset).tolist())
                            for motor in self.motor_positions]
        torques = np.cross(shifted_positons, self.motor_thrusts)

        return [
            [thrust[0] for thrust in self.motor_thrusts], # Fx (N)
            [thrust[1] for thrust in self.motor_thrusts], # Fy (N)
            [thrust[2] for thrust in self.motor_thrusts], # Fz (N)
            [torque[0] for torque in torques],            # Rx (N*m)
            [torque[1] for torque in torques],            # Ry (N*m)
            [torque[2] for torque in torques]             # Rz (N*m)
        ]
    
    def generate_motor_values(self, twist_msg: Twist):
        twist_array = [
            twist_msg.linear.x  * MAX_FWD_THRUST,   # escala a Newtons reales
            twist_msg.linear.y  * MAX_FWD_THRUST,
            twist_msg.linear.z  * MAX_FWD_THRUST,
            twist_msg.angular.x * 5.0,   # escala a N·m (ajusta según el ROV)
            twist_msg.angular.y * 5.0,
            twist_msg.angular.z * 5.0,
        ]

        if all(v == 0 for v in twist_array):
            return [0.0] * 6

        motor_values = np.matmul(self.inverse_config, twist_array).tolist()

        # Clampear al límite físico de cada thruster
        result = []
        for v in motor_values:
            if v > MAX_FWD_THRUST:
                v = MAX_FWD_THRUST
            elif v < MAX_REV_THRUST:
                v = MAX_REV_THRUST
            result.append(v)

        return result
    
    
    def thrust_callback(self, twist_msg):
        thrust_msg = Float32MultiArray()
        thrust_msg.data = self.generate_motor_values(twist_msg)
        self.thrust_pub.publish(thrust_msg)
        

def main(args=None):
    rclpy.init(args=args)
    node = twist_to_newtons()
    try: 
        rclpy.spin(node)
    except KeyboardInterrupt:
        del node
        rclpy.shutdown()    


if __name__ == "__main__":
    main(sys.argv)