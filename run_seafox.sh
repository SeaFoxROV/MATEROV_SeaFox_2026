#!/bin/bash

cleanup() {
    echo -e "\n[INFO] Cerrando procesos..."

    # Matar grupos completos (incluye hijos de ROS2)
    kill -TERM -"$ROS_PID" 2>/dev/null
    kill -TERM -"$GUI_PID" 2>/dev/null

    wait "$ROS_PID" 2>/dev/null
    wait "$GUI_PID" 2>/dev/null

    echo "[INFO] Todo cerrado correctamente"
    exit 0
}

# Capturar señales importantes
trap cleanup SIGINT SIGTERM EXIT

# Source ROS
source /opt/ros/humble/setup.bash
source /home/ever/MATEROV_SeaFox_2026/ros2_ws/install/setup.bash

# Lanzar ROS2 en su propio grupo
setsid ros2 launch seafox_rov_2026 control_launch.py &
ROS_PID=$!

# Lanzar GUI en su propio grupo
setsid python3 /home/ever/MATEROV_SeaFox_2026/ros2_ws/src/seafox_rov_2026/seafox_rov_2026/pilot_gui/main_window.py &
GUI_PID=$!

# Esperar GUI
wait "$GUI_PID"

cleanup