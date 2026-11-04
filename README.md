# MATEROV SeaFox 2026

Software del **Seafox Inventive Team** para la competencia **MATE ROV 2026**. El repositorio incluye las interfaces gráficas del piloto y del copiloto, la detección de cangrejos por visión artificial (YOLO), herramientas para las tareas de misión (fotogrametría, icebergs, eDNA) y paquetes de ROS 2 para simular y visualizar el ROV en RViz.

## Video de demostración

[![Demostración del ROV SeaFox](https://img.youtube.com/vi/cpsMytgSRSA/hqdefault.jpg)](https://www.youtube.com/watch?v=cpsMytgSRSA)

Mira el funcionamiento del ROV en YouTube: <https://www.youtube.com/watch?v=cpsMytgSRSA>

---

## Arquitectura general

```
┌─────────────────────────┐        WebSocket (puerto 3001)        ┌──────────────────────────┐
│   Pilot GUI (PyQt5)     │ ────────────────────────────────────▶ │   Copilot GUI (PyQt5)    │
│  - 3 cámaras IP (HTTP)  │   snapshots + detecciones (JSON+JPEG) │  - Photogrammetry        │
│  - Ajuste de imagen     │                                       │  - Iceberg               │
│  - Detección YOLO       │                                       │  - Crab Vision           │
└─────────────────────────┘                                       │  - eDNA                  │
                                                                  └──────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│ ROS 2 Humble (ros2_ws)                                         │
│  seafox_sim_2026: URDF + RViz, profundidad (/depth) y fuerzas  │
│  seafox_rov_2026: código del ROV y GUI del piloto              │
│  seafox_float_2026: paquete del flotador (en desarrollo)       │
└───────────────────────────────────────────────────────────────┘
```

## Estructura del repositorio

| Ruta | Descripción |
|------|-------------|
| `ros2_ws/src/seafox_rov_2026/seafox_rov_2026/pilot_gui/` | GUI del piloto: visualiza las cámaras IP, ajusta brillo/contraste/saturación, ejecuta la detección de cangrejos y envía capturas al copiloto. |
| `ros2_ws/src/seafox_rov_2026/.../pilot_gui/lib/vision/` | Detector de cangrejos (`crabDetection.py`) con el modelo YOLO `best.pt`. |
| `ros2_ws/src/seafox_sim_2026/` | Simulación en RViz: modelo URDF del ROV, nodo de TF por profundidad (`/depth`) y visualizador de fuerzas (`/desired_force`, `/perceived_force`). |
| `ros2_ws/src/seafox_float_2026/` | Paquete ROS 2 del flotador (esqueleto). |
| `copilot_ws/src/gui/` | GUI del copiloto con pestañas: **Photogrammetry**, **Iceberg**, **Crab Vision** y **eDNA**. Abre un servidor WebSocket en el puerto `3001`. |
| `copilot_ws/src/gui/components/runs/detect/train/` | Resultados y pesos del entrenamiento YOLO. |
| `websocket.py` | Servidor WebSocket independiente (relay/broadcast en el puerto `3001`) para pruebas. |
| `caliz_2.py` | Cliente de prueba: envía una imagen (`test.png`) y cajas de detección simuladas al copiloto. |
| `caliz.py` | Visor de prueba de un tópico de imagen ROS 2 (`/mainCamera`). |
| `dockerfile` | Imagen con ROS 2 Humble, PyQt5 y OpenCV para desarrollo. |
| `run.bat` | Lanzador de la GUI del piloto en Windows. |

---

## Requisitos

- **Python 3.11** (recomendado; es el que usa `run.bat`)
- **ROS 2 Humble** (solo para los paquetes de `ros2_ws`; en Ubuntu 22.04 o con Docker)
- Cámaras IP accesibles en la red del ROV (para la GUI del piloto)

Dependencias de Python principales: `PyQt5`, `opencv-python`, `numpy`, `ultralytics`, `torch`, `requests`, `pyqtgraph`, `websockets`.

---

## Instalación

```bash
git clone <url-del-repo> MATEROV_SeaFox_2026
cd MATEROV_SeaFox_2026

# Crear y activar un entorno virtual
python3.11 -m venv venv311
source venv311/bin/activate          # Windows: venv311\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install PyQt5 pyqtgraph websockets
```

> `requirements.txt` está guardado en UTF‑16. Si `pip` da error al leerlo, conviértelo a UTF‑8 (por ejemplo, con `iconv -f UTF-16 -t UTF-8 requirements.txt > req.txt`) e instala desde `req.txt`.

---

## Ejecución

### 1. GUI del copiloto

Inicia el servidor WebSocket en el puerto `3001` y muestra las pestañas de misión.

```bash
cd copilot_ws/src/gui
python main.py
```

### 2. GUI del piloto

Antes de ejecutarla, revisa las direcciones de red:

- **Cámaras IP**: `camera_configs` en `pilot_gui/components/camera.py` (por defecto `192.168.1.67`, `.68` y `.69`).
- **IP del copiloto**: `ws_url` en `pilot_gui/components/websocket.py` (por defecto `ws://10.4.65.90:3001`).

```bash
cd ros2_ws/src/seafox_rov_2026/seafox_rov_2026/pilot_gui
python main_window.py
```

En Windows, desde la raíz del repositorio:

```bat
run.bat
```

#### Controles de teclado (GUI del piloto)

| Tecla | Acción |
|-------|--------|
| `1` / `2` / `3` | Seleccionar cámara principal / superior / media (pulsar dos veces para maximizar). |
| `0` | Seleccionar todas las cámaras. |
| `Esc` | Restablecer la vista de cámaras. |
| `Espacio` | Enviar un snapshot de la cámara seleccionada al copiloto. |
| `D` / `d` | Iniciar / detener la detección de cangrejos. |
| `E` | Enviar la detección actual (imagen y cajas) al copiloto. |
| `B` / `b` | Subir / bajar el brillo. |
| `C` / `c` | Subir / bajar el contraste. |
| `S` / `s` | Subir / bajar la saturación. |

### 3. Probar la comunicación sin el ROV

Con la GUI del copiloto abierta, envía una detección simulada desde la raíz del repositorio:

```bash
python caliz_2.py
```

Si quieres un relay WebSocket independiente en lugar de la GUI del copiloto:

```bash
python websocket.py
```

### 4. Simulación en ROS 2 (RViz)

```bash
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash

ros2 launch seafox_sim_2026 display.launch.py
```

Para mover el ROV en profundidad o visualizar fuerzas, publica en los tópicos:

```bash
ros2 topic pub /depth std_msgs/msg/Float32 "{data: 1.5}"
ros2 topic pub /desired_force geometry_msgs/msg/Vector3Stamped "{vector: {x: 1.0, y: 0.0, z: 0.0}}"
```

### 5. Docker (opcional)

```bash
docker build -t seafox-ros .
docker run -it --rm \
  -v $(pwd)/ros2_ws:/home/ros/ros2_ws \
  seafox-ros
```

> Para abrir RViz o las GUIs desde el contenedor hay que habilitar X11 (por ejemplo, con `-e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix` en Linux).

---

## Protocolo WebSocket Pilot → Copilot

Cada mensaje es binario con el siguiente formato:

```
[ 4 bytes: longitud del JSON (little-endian) ][ JSON UTF-8 ][ imagen JPEG ]
```

Ejemplo del JSON:

```json
{ "type": "crab_detection", "boxes": [[x1, y1, x2, y2], ...], "count": 2 }
```

---

## Licencia

Distribuido bajo los términos indicados en [`LICENSE`](LICENSE).
