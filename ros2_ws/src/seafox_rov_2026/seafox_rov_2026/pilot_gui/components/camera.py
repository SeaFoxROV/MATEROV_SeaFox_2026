from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class CameraWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.cameras = {
            "upper":"http://admin:admin@192.168.1.9:6688/snapshot/PROFILE_000",
            "middle":"http://admin:admin@192.168.1.4:6688/snapshot/PROFILE_000",
            # "bottom":"http://admin:admin@192.168.1.4:6688/snapshot/PROFILE_000"
        }

        self.setFrameShape(QFrame.StyledPanel)

        main_layout = QVBoxLayout()

        for name, url in self.cameras.items():
            camera_layout = QVBoxLayout()

            title = QLabel(name.upper())
            title.setAlignment(Qt.AlignCenter)

            image_label = QLabel("Stream")
            image_label.setAlignment(Qt.AlignCenter)

            camera_layout.addWidget(title)
            camera_layout.addWidget(image_label)

            main_layout.addLayout(camera_layout)

        self.setLayout(main_layout  )
