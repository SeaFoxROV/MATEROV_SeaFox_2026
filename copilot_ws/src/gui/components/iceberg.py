from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class Iceberg(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Esta es la página Iceberg"))

        self.setLayout(layout)