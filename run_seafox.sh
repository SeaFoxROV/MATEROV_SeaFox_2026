#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
ROS_WS="$PROJECT_ROOT/ros2_ws"

cleanup() {
    echo -e "\n[INFO] Cerrando procesos..."

    kill -TERM -"$ROS_PID" 2>/dev/null
    kill -TERM -"$GUI_PID" 2>/dev/null

    wait "$ROS_PID" 2>/dev/null
    wait "$GUI_PID" 2>/dev/null

    echo "[INFO] Todo cerrado correctamente"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "[INFO] Proyecto: $PROJECT_ROOT"

# ROS Humble
source /opt/ros/humble/setup.bash

# Workspace local
source "$ROS_WS/install/setup.bash"

# Lanzar ROS
setsid ros2 launch seafox_rov_2026 control_launch.py &
ROS_PID=$!

# Esperar un poco para que ROS arranque
sleep 2

# Lanzar GUI
setsid python3 \
"$ROS_WS/src/seafox_rov_2026/seafox_rov_2026/pilot_gui/main_window.py" &
GUI_PID=$!

wait "$GUI_PID"

cleanup