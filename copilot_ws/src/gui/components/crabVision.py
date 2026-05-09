from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class crabVision(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Esta es la página crabVision"))

        self.setLayout(layout)