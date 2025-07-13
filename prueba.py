import sys
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel


class PruebaSonido(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔊 Prueba de sonido")
        self.setMinimumSize(300, 150)

        layout = QVBoxLayout()
        self.label = QLabel("Presioná el botón para reproducir el sonido:")
        self.label.setWordWrap(True)

        self.boton = QPushButton("🔔 Reproducir beep")
        self.boton.clicked.connect(self.reproducir_sonido)

        layout.addWidget(self.label)
        layout.addWidget(self.boton)
        self.setLayout(layout)

        # Ruta absoluta al archivo WAV
        ruta_audio = Path("sonidos/beep.wav").resolve()
        self.sonido = QSoundEffect()
        self.sonido.setSource(QUrl.fromLocalFile(str(ruta_audio)))
        self.sonido.setVolume(1.0)

    def reproducir_sonido(self):
        self.sonido.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PruebaSonido()
    ventana.show()
    sys.exit(app.exec())
