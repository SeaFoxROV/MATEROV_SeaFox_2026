import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QTextEdit,
    QHBoxLayout,
    QLabel,
)


class Ventana(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tabla de Especies")
        self.resize(600, 400)

        layout = QVBoxLayout()

        # Crear tabla de 10 filas y 3 columnas
        self.tabla = QTableWidget(11, 3)
        self.tabla.setHorizontalHeaderLabels(["Especie", "Cantidad", "Porcentaje (%)"])
        self.tabla.setItem(10, 0, QTableWidgetItem("TOTAL"))

        layout.addWidget(self.tabla)

        self.texto = QTextEdit()
        self.texto.setPlaceholderText("Ingrese datos aquί: ")
        layout.addWidget(QLabel("Ingreso por texto:"))
        layout.addWidget(self.texto)

        self.boton_cargar = QPushButton("Cargar desde texto")
        self.boton_cargar.clicked.connect(self.cargar_desde_texto)
        layout.addWidget(self.boton_cargar)

        # Botón para calcular porcentajes
        self.boton = QPushButton("Calcular porcentajes")
        self.boton.clicked.connect(self.calcular_porcentajes)
        layout.addWidget(self.boton)

        self.setLayout(layout)

    def calcular_porcentajes(self):
        total = 0

        # Calcular total
        for fila in range(10):
            item = self.tabla.item(fila, 1)
            if item:
                try:
                    total += int(item.text())
                except:
                    pass

        # Calcular porcentajes
        for fila in range(10):
            item = self.tabla.item(fila, 1)
            if item and total > 0:
                try:
                    cantidad = int(item.text())
                    porcentaje = (cantidad / total) * 100
                    self.tabla.setItem(fila, 2, QTableWidgetItem(f"{porcentaje:.2f}"))
                except:
                    pass
        self.tabla.setItem(10, 1, QTableWidgetItem(str(total)))
        self.tabla.setItem(10, 2, QTableWidgetItem("100%"))

    def cargar_desde_texto(self):

        # limpiar solo filas de especies
        for fila in range(10):
            for col in range(3):
                self.tabla.setItem(fila, col, None)

        contenido = self.texto.toPlainText()
        lineas = contenido.splitlines()

        fila = 0

        for linea in lineas:
            if fila >= 10:
                break

            linea = linea.strip()

            if not linea:
                continue

            # separar especie y cantidad
            partes = linea.rsplit(maxsplit=1)

            if len(partes) == 2:
                especie = partes[0]
                cantidad = partes[1]

                self.tabla.setItem(fila, 0, QTableWidgetItem(especie))
                self.tabla.setItem(fila, 1, QTableWidgetItem(cantidad))

                fila += 1


app = QApplication(sys.argv)
ventana = Ventana()
ventana.show()
sys.exit(app.exec_())
