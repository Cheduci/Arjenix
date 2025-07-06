from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QProgressBar
)
from bbdd import db_config
from PySide6.QtCore import Qt
import bcrypt
import re

class CambioPasswordDialog(QDialog):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("🔐 Cambio de contraseña")
        self.setFixedSize(350, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Hola {self.sesion['nombre']}, por seguridad debés establecer una nueva contraseña."))

        self.nueva_clave = QLineEdit()
        self.nueva_clave.setPlaceholderText("Nueva contraseña")
        self.nueva_clave.setEchoMode(QLineEdit.Password)
        self.nueva_clave.textChanged.connect(self.evaluar_fuerza)
        layout.addWidget(self.nueva_clave)

        self.fuerza = QProgressBar()
        self.fuerza.setMaximum(100)
        self.fuerza.setTextVisible(False)
        self.fuerza.setFixedHeight(10)
        layout.addWidget(self.fuerza)

        self.confirmar = QLineEdit()
        self.confirmar.setPlaceholderText("Confirmar contraseña")
        self.confirmar.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirmar)

        btn = QPushButton("Guardar")
        btn.clicked.connect(self.actualizar_password)
        layout.addWidget(btn)

        self.setLayout(layout)

    def evaluar_fuerza(self, texto: str):
        puntaje = 0
        if len(texto) >= 6:
            puntaje += 30
        if re.search(r"[A-Z]", texto):
            puntaje += 20
        if re.search(r"[0-9]", texto):
            puntaje += 20
        if re.search(r"[\W_]", texto):  # símbolos
            puntaje += 30

        self.fuerza.setValue(puntaje)

        # Cambia color según fuerza
        if puntaje < 40:
            self.fuerza.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif puntaje < 70:
            self.fuerza.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.fuerza.setStyleSheet("QProgressBar::chunk { background-color: green; }")

    def actualizar_password(self):
        clave = self.nueva_clave.text().strip()
        confirm = self.confirmar.text().strip()

        if not clave or not confirm:
            QMessageBox.warning(self, "Campos requeridos", "Completá ambos campos.")
            return

        if clave != confirm:
            QMessageBox.warning(self, "No coinciden", "Las contraseñas ingresadas no coinciden.")
            return

        if len(clave) < 6:
            QMessageBox.warning(self, "Débil", "La nueva contraseña debe tener al menos 6 caracteres.")
            return

        try:
            conn = db_config.conectar_db()
            cur = conn.cursor()

            hashpw = bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode()

            cur.execute("""
                UPDATE usuarios
                SET password_hash = %s,
                    debe_cambiar_password = FALSE
                WHERE id = %s
            """, (hashpw, self.sesion["id"]))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Listo", "Contraseña actualizada correctamente.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la contraseña.\n{e}")
