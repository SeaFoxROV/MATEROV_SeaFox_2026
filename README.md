# MATEROV SeaFox 2026

Software by the **Seafox Inventive Team** for the **MATE ROV 2026** competition. The repository includes the pilot and copilot graphical interfaces, crab detection using computer vision (YOLO), tools for mission tasks (photogrammetry, icebergs, eDNA), and ROS 2 packages to simulate and visualize the ROV in RViz.

## Demo video

[![SeaFox ROV demo](https://img.youtube.com/vi/cpsMytgSRSA/hqdefault.jpg)](https://www.youtube.com/watch?v=cpsMytgSRSA)

Watch the ROV in action on YouTube: <https://www.youtube.com/watch?v=cpsMytgSRSA>

---

## Overall architecture

```
┌─────────────────────────┐        WebSocket (port 3001)          ┌──────────────────────────┐
│   Pilot GUI (PyQt5)     │ ────────────────────────────────────▶ │   Copilot GUI (PyQt5)    │
│  - 3 IP cameras (HTTP)  │   snapshots + detections (JSON+JPEG)  │  - Photogrammetry        │
│  - Image adjustment     │                                       │  - Iceberg               │
│  - YOLO detection       │                                       │  - Crab Vision           │
└─────────────────────────┘                                       │  - eDNA                  │
                                                                  └──────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│ ROS 2 Humble (ros2_ws)                                         │
│  seafox_sim_2026: URDF + RViz, depth (/depth) and forces       │
│  seafox_rov_2026: ROV code and pilot GUI                       │
│  seafox_float_2026: float package (in development)             │
└───────────────────────────────────────────────────────────────┘
```

## Repository structure

| Path | Description |
|------|-------------|
| `ros2_ws/src/seafox_rov_2026/seafox_rov_2026/pilot_gui/` | Pilot GUI: displays the IP cameras, adjusts brightness/contrast/saturation, runs crab detection, and sends captures to the copilot. |
| `ros2_ws/src/seafox_rov_2026/.../pilot_gui/lib/vision/` | Crab detector (`crabDetection.py`) using the YOLO model `best.pt`. |
| `ros2_ws/src/seafox_sim_2026/` | RViz simulation: ROV URDF model, depth-based TF node (`/depth`), and force visualizer (`/desired_force`, `/perceived_force`). |
| `ros2_ws/src/seafox_float_2026/` | ROS 2 float package (skeleton). |
| `copilot_ws/src/gui/` | Copilot GUI with tabs: **Photogrammetry**, **Iceberg**, **Crab Vision**, and **eDNA**. Opens a WebSocket server on port `3001`. |
| `copilot_ws/src/gui/components/runs/detect/train/` | YOLO training results and weights. |
| `websocket.py` | Standalone WebSocket server (relay/broadcast on port `3001`) for testing. |
| `caliz_2.py` | Test client: sends an image (`test.png`) and simulated detection boxes to the copilot. |
| `caliz.py` | Test viewer for a ROS 2 image topic (`/mainCamera`). |
| `dockerfile` | Image with ROS 2 Humble, PyQt5, and OpenCV for development. |
| `run.bat` | Pilot GUI launcher for Windows. |

---

## Requirements

- **Python 3.11** (recommended; it is the version used by `run.bat`)
- **ROS 2 Humble** (only for the `ros2_ws` packages; on Ubuntu 22.04 or via Docker)
- IP cameras reachable on the ROV network (for the pilot GUI)

Main Python dependencies: `PyQt5`, `opencv-python`, `numpy`, `ultralytics`, `torch`, `requests`, `pyqtgraph`, `websockets`.

---

## Installation

```bash
git clone <repo-url> MATEROV_SeaFox_2026
cd MATEROV_SeaFox_2026

# Create and activate a virtual environment
python3.11 -m venv venv311
source venv311/bin/activate          # Windows: venv311\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install PyQt5 pyqtgraph websockets
```

> `requirements.txt` is saved in UTF‑16. If `pip` fails to read it, convert it to UTF‑8 (for example, with `iconv -f UTF-16 -t UTF-8 requirements.txt > req.txt`) and install from `req.txt`.

---

## Running

### 1. Copilot GUI

Starts the WebSocket server on port `3001` and shows the mission tabs.

```bash
cd copilot_ws/src/gui
python main.py
```

### 2. Pilot GUI

Before running it, check the network addresses:

- **IP cameras**: `camera_configs` in `pilot_gui/components/camera.py` (defaults: `192.168.1.67`, `.68`, and `.69`).
- **Copilot IP**: `ws_url` in `pilot_gui/components/websocket.py` (default: `ws://10.4.65.90:3001`).

```bash
cd ros2_ws/src/seafox_rov_2026/seafox_rov_2026/pilot_gui
python main_window.py
```

On Windows, from the repository root:

```bat
run.bat
```

#### Keyboard controls (pilot GUI)

| Key | Action |
|-----|--------|
| `1` / `2` / `3` | Select main / top / middle camera (press twice to maximize). |
| `0` | Select all cameras. |
| `Esc` | Reset the camera view. |
| `Space` | Send a snapshot of the selected camera to the copilot. |
| `D` / `d` | Start / stop crab detection. |
| `E` | Send the current detection (image and boxes) to the copilot. |
| `B` / `b` | Increase / decrease brightness. |
| `C` / `c` | Increase / decrease contrast. |
| `S` / `s` | Increase / decrease saturation. |

### 3. Testing communication without the ROV

With the copilot GUI open, send a simulated detection from the repository root:

```bash
python caliz_2.py
```

If you want a standalone WebSocket relay instead of the copilot GUI:

```bash
python websocket.py
```

### 4. ROS 2 simulation (RViz)

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash

ros2 launch seafox_sim_2026 display.launch.py
```

To move the ROV in depth or visualize forces, publish to these topics:

```bash
ros2 topic pub /depth std_msgs/msg/Float32 "{data: 1.5}"
ros2 topic pub /desired_force geometry_msgs/msg/Vector3Stamped "{vector: {x: 1.0, y: 0.0, z: 0.0}}"
```

### 5. Docker (optional)

```bash
docker build -t seafox-ros .
docker run -it --rm \
  -v $(pwd)/ros2_ws:/home/ros/ros2_ws \
  seafox-ros
```

> To open RViz or the GUIs from the container you need to enable X11 (for example, with `-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix` on Linux).

---

## Pilot → Copilot WebSocket protocol

Each message is binary with the following format:

```
[ 4 bytes: JSON length (little-endian) ][ UTF-8 JSON ][ JPEG image ]
```

Example JSON:

```json
{ "type": "crab_detection", "boxes": [[x1, y1, x2, y2], ...], "count": 2 }
```

---

## License

Distributed under the terms specified in [`LICENSE`](LICENSE).
