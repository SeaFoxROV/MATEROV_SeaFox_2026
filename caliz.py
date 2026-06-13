#!/usr/bin/env python3

import pygame
import rclpy

from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray


class KeyboardController(Node):

    def __init__(self):
        super().__init__('keyboard_controller')

        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/desired_twist',
            10
        )

        self.gripper_pub = self.create_publisher(
            Float32MultiArray,
            '/gripper_pwm',
            10
        )

        pygame.init()

        self.screen = pygame.display.set_mode((400, 150))
        pygame.display.set_caption("ROV Keyboard Control")

        # Valores actuales
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0

        self.current_pitch = 0.0
        self.current_yaw = 0.0

        # Velocidad de rampa
        self.step = 0.05

        # Timer a 30 Hz
        self.timer = self.create_timer(
            1.0 / 30.0,
            self.update
        )

        self.get_logger().info("Keyboard controller iniciado")

    def approach(self, current, target, step):
        if current < target:
            return min(current + step, target)

        if current > target:
            return max(current - step, target)

        return current

    def update(self):

        # Procesar eventos de pygame
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                rclpy.shutdown()
                return

        keys = pygame.key.get_pressed()

        cmd = Twist()

        # ==========================
        # TARGETS
        # ==========================

        target_x = 0.0
        target_y = 0.0
        target_z = 0.0

        target_pitch = 0.0
        target_yaw = 0.0

        # W/S -> X
        if keys[pygame.K_w]:
            target_x = 1.0
        elif keys[pygame.K_s]:
            target_x = -1.0

        # A/D -> Y
        if keys[pygame.K_a]:
            target_y = 1.0
        elif keys[pygame.K_d]:
            target_y = -1.0

        # P/O -> Z
        if keys[pygame.K_p]:
            target_z = 1.0
        elif keys[pygame.K_o]:
            target_z = -1.0

        # Flechas arriba/abajo -> angular.x
        if keys[pygame.K_UP]:
            target_pitch = 1.0
        elif keys[pygame.K_DOWN]:
            target_pitch = -1.0

        # Flechas izquierda/derecha -> angular.z
        if keys[pygame.K_LEFT]:
            target_yaw = 1.0
        elif keys[pygame.K_RIGHT]:
            target_yaw = -1.0

        # ==========================
        # RAMPAS
        # ==========================

        self.current_x = self.approach(
            self.current_x,
            target_x,
            self.step
        )

        self.current_y = self.approach(
            self.current_y,
            target_y,
            self.step
        )

        self.current_z = self.approach(
            self.current_z,
            target_z,
            self.step
        )

        self.current_pitch = self.approach(
            self.current_pitch,
            target_pitch,
            self.step
        )

        self.current_yaw = self.approach(
            self.current_yaw,
            target_yaw,
            self.step
        )

        # ==========================
        # TWIST
        # ==========================

        cmd.linear.x = self.current_x
        cmd.linear.y = self.current_y
        cmd.linear.z = self.current_z

        cmd.angular.x = self.current_pitch
        cmd.angular.y = 0.0
        cmd.angular.z = self.current_yaw

        # ==========================
        # GRIPPER
        # ==========================

        gripper = Float32MultiArray()

        if keys[pygame.K_g]:
            gripper.data = [1900.0]
        else:
            gripper.data = [1200.0]

        # ==========================
        # PUBLICAR
        # ==========================

        self.cmd_vel_pub.publish(cmd)
        self.gripper_pub.publish(gripper)

        # Debug opcional
        print(
            f"X:{cmd.linear.x: .2f} "
            f"Y:{cmd.linear.y: .2f} "
            f"Z:{cmd.linear.z: .2f} "
            f"Pitch:{cmd.angular.x: .2f} "
            f"Yaw:{cmd.angular.z: .2f}",
            end="\r"
        )

    def destroy(self):
        pygame.quit()
        self.destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = KeyboardController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    pygame.quit()

    if rclpy.ok():
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()