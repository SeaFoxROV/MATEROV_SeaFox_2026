from PyQt5.QtWidgets import (
    QWidget, QApplication, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QGridLayout, QSpinBox,
    QComboBox, QHBoxLayout, QLineEdit
)

import sys
import math
import pyqtgraph as pg


class Iceberg(QWidget):

    # precarga de datos por plataforma
    platforms = [
        {"name": "Hibernia", "lat": 46.7504, "lon": -48.7819, "depth": 78},
        {"name": "Hebron", "lat": 46.544, "lon": -48.518, "depth": 93},
        {"name": "Sea Rose", "lat": 46.7895, "lon": -48.146, "depth": 107},
        {"name": "Terra Nova", "lat": 46.4, "lon": -48.4, "depth": 91},
    ]

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Iceberg Risk Detection")
        self.resize(700, 500)

        layout = QGridLayout()

        input_iceberg = QVBoxLayout()
        platforms_table = QVBoxLayout()
        icebergmap_layout = QVBoxLayout()

        # GRAFICA
        self.graph = pg.PlotWidget()
        self.graph.showGrid(x=True, y=True)
        self.graph.setLabel('left', 'Latitude')
        self.graph.setLabel('bottom', 'Longitude')

        icebergmap_layout.addWidget(QLabel("Iceberg Map"))
        icebergmap_layout.addWidget(self.graph)

        # TABLA
        self.tabla = QTableWidget(len(self.platforms), 7)

        self.tabla.setHorizontalHeaderLabels([
            "Platform",
            "Latitude",
            "Longitude",
            "Depth",
            "Min Dist (nm)",
            "Surface Risk",
            "Subsea Risk"
        ])

        for fila, p in enumerate(self.platforms):

            self.tabla.setItem(
                fila, 0,
                QTableWidgetItem(p["name"])
            )

            self.tabla.setItem(
                fila, 1,
                QTableWidgetItem(str(p["lat"]))
            )

            self.tabla.setItem(
                fila, 2,
                QTableWidgetItem(str(p["lon"]))
            )

            self.tabla.setItem(
                fila, 3,
                QTableWidgetItem(str(p["depth"]))
            )

            self.tabla.setItem(fila, 4, QTableWidgetItem(""))
            self.tabla.setItem(fila, 5, QTableWidgetItem(""))
            self.tabla.setItem(fila, 6, QTableWidgetItem(""))

        platforms_table.addWidget(QLabel("Platforms"))
        platforms_table.addWidget(self.tabla)

        # INPUTS

        # LAT
        lat_layout = QHBoxLayout()

        self.lat_deg = QSpinBox()
        self.lat_deg.setRange(0, 180)

        self.lat_min = QSpinBox()
        self.lat_min.setRange(0, 59)

        self.lat_sec = QSpinBox()
        self.lat_sec.setRange(0, 59)

        self.lat_dir = QComboBox()
        self.lat_dir.addItems(["N", "S"])

        lat_layout.addWidget(QLabel("Lat:"))
        lat_layout.addWidget(self.lat_deg)
        lat_layout.addWidget(QLabel("°"))
        lat_layout.addWidget(self.lat_min)
        lat_layout.addWidget(QLabel("'"))
        lat_layout.addWidget(self.lat_sec)
        lat_layout.addWidget(QLabel('"'))
        lat_layout.addWidget(self.lat_dir)

        # LON
        lon_layout = QHBoxLayout()

        self.lon_deg = QSpinBox()
        self.lon_deg.setRange(0, 180)

        self.lon_min = QSpinBox()
        self.lon_min.setRange(0, 59)

        self.lon_sec = QSpinBox()
        self.lon_sec.setRange(0, 59)

        self.lon_dir = QComboBox()
        self.lon_dir.addItems(["E", "W"])

        lon_layout.addWidget(QLabel("Lon:"))
        lon_layout.addWidget(self.lon_deg)
        lon_layout.addWidget(QLabel("°"))
        lon_layout.addWidget(self.lon_min)
        lon_layout.addWidget(QLabel("'"))
        lon_layout.addWidget(self.lon_sec)
        lon_layout.addWidget(QLabel('"'))
        lon_layout.addWidget(self.lon_dir)

        # HEADING
        heading_layout = QHBoxLayout()

        self.heading_spinbox = QSpinBox()
        self.heading_spinbox.setRange(0, 360)

        heading_layout.addWidget(QLabel("Heading:"))
        heading_layout.addWidget(self.heading_spinbox)

        # KEEL
        keel_layout = QHBoxLayout()

        self.keel_input = QLineEdit()

        keel_layout.addWidget(QLabel("Keel:"))
        keel_layout.addWidget(self.keel_input)

        # BOTON
        self.boton = QPushButton("Calculate")
        self.boton.clicked.connect(self.show_results)

        # COMPOSICION
        left = QVBoxLayout()
        right = QVBoxLayout()

        left.addWidget(QLabel("Latitude"))
        left.addLayout(lat_layout)

        left.addWidget(QLabel("Longitude"))
        left.addLayout(lon_layout)

        top_right = QHBoxLayout()

        top_right.addLayout(heading_layout)
        top_right.addLayout(keel_layout)

        right.addLayout(top_right)
        right.addWidget(self.boton)

        input_main = QHBoxLayout()

        input_main.addLayout(left)
        input_main.addLayout(right)

        input_iceberg.addWidget(QLabel("Iceberg Data"))
        input_iceberg.addLayout(input_main)

        # GRID FINAL
        layout.addLayout(input_iceberg, 0, 0)
        layout.addLayout(platforms_table, 1, 0)
        layout.addLayout(icebergmap_layout, 0, 1, 2, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)

        self.setLayout(layout)

        # dibujar plataformas
        self.draw_platforms()

    # FUNCIONES

    def miles_to_decimal(self, degree, minutes, seconds, posicion):

        decimal_posicion = (
            degree +
            minutes / 60 +
            seconds / 3600
        )

        return (
            -decimal_posicion
            if posicion in ["S", "W"]
            else decimal_posicion
        )

    def calcular_riesgos(
        self,
        lat0,
        lon0,
        heading,
        keel_depth
    ):

        theta = math.radians(heading)

        for p in self.platforms:
            p["min_dist"] = float("inf")

        def distance_nm(lat1, lon1, lat2, lon2):

            dlat = (lat1 - lat2) * 60

            dlon = (
                (lon1 - lon2)
                * 60
                * math.cos(math.radians(lat2))
            )

            return math.sqrt(dlat**2 + dlon**2)

        max_steps = 2000
        step_nm = 0.1

        lat = lat0
        lon = lon0

        trayectoria = []

        for _ in range(max_steps):

            lat += (
                (step_nm / 60)
                * math.cos(theta)
            )

            lon += (
                step_nm /
                (60 * math.cos(math.radians(lat)))
            ) * math.sin(theta)

            trayectoria.append((lat, lon))

            for p in self.platforms:

                distance = distance_nm(
                    lat,
                    lon,
                    p["lat"],
                    p["lon"]
                )

                if distance < p["min_dist"]:
                    p["min_dist"] = distance

        def surface_risk(keel, min_dist, depth):

            if keel >= (1.1 * depth):
                return "GREEN"

            elif min_dist > 10:
                return "GREEN"

            elif min_dist >= 5:
                return "YELLOW"

            else:
                return "RED"

        def subsea_risk(keel, depth, d):

            if d > 25:
                return "GREEN"

            elif (keel / depth) >= 1.10:
                return "GREEN"

            elif (keel / depth) >= 0.90:
                return "RED"

            elif (keel / depth) >= 0.70:
                return "YELLOW"

            else:
                return "GREEN"

        resultados = []

        for p in self.platforms:

            resultados.append({
                "depth": p["depth"],
                "name": p["name"],
                "min_dist": p["min_dist"],
                "surface": surface_risk(
                    keel_depth,
                    p["min_dist"],
                    p["depth"]
                ),
                "subsea": subsea_risk(
                    keel_depth,
                    p["depth"],
                    p["min_dist"]
                )
            })

        return resultados, trayectoria

    def draw_platforms(self, resultados=None):

        self.graph.clear()

        for i, p in enumerate(self.platforms):

            color = 'w'

            if resultados:

                risk = resultados[i]["surface"]

                if risk == "GREEN":
                    color = 'g'

                elif risk == "YELLOW":
                    color = 'y'

                else:
                    color = 'r'

            self.graph.plot(
                [p["lon"]],
                [p["lat"]],
                pen=None,
                symbol='o',
                symbolBrush=color,
                symbolSize=10
            )

    def show_results(self):

        try:

            lat0 = self.miles_to_decimal(
                self.lat_deg.value(),
                self.lat_min.value(),
                self.lat_sec.value(),
                self.lat_dir.currentText()
            )

            lon0 = self.miles_to_decimal(
                self.lon_deg.value(),
                self.lon_min.value(),
                self.lon_sec.value(),
                self.lon_dir.currentText()
            )

            heading = self.heading_spinbox.value()

            keel_depth = float(
                self.keel_input.text()
            )

        except Exception as e:

            print("Error:", e)
            return

        resultados, trayectoria = self.calcular_riesgos(
            lat0,
            lon0,
            heading,
            keel_depth
        )

        # llenar tabla
        for fila, r in enumerate(resultados):

            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem(
                    str(round(r["min_dist"], 2))
                )
            )

            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem(r["surface"])
            )

            self.tabla.setItem(
                fila,
                6,
                QTableWidgetItem(r["subsea"])
            )

        # dibujar plataformas
        self.draw_platforms(resultados)

        # trayectoria
        lats = [p[0] for p in trayectoria]
        lons = [p[1] for p in trayectoria]

        self.graph.plot(
            lons,
            lats,
            pen='b'
        )


