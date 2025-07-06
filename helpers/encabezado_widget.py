from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os


class EncabezadoWidget(QWidget):
    def __init__(self, sesion: dict, ruta_logo: str = "ui/Arjenix_transparente.png"):
        super().__init__()
        self.sesion = sesion
        self.ruta_logo = ruta_logo
        self.setup_ui()
        

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(25, 5, 25, 5)

        # 🖼️ Logo (izquierda)
        logo = QLabel()
        pixmap = QPixmap(self.ruta_logo).scaledToHeight(80, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(logo)

        layout.addStretch()

        # 👋 Saludo (derecha)
        nombre = self.sesion.get("nombre", "")
        apellido = self.sesion.get("apellido", "")
        saludo = QLabel(f"👋 ¡Hola {nombre} {apellido}!")
        saludo.setStyleSheet("font-weight: bold; font-size: 14px; margin-right: 12px;")
        saludo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(saludo)

        self.setLayout(layout)
        self.setFixedHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)