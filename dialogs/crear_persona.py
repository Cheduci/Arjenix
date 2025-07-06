from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QDateEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import QDate
from core.personas import dni_existe
import re

class CrearPersonaDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("👤 Nueva persona")
        self.setMinimumSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.dni = QLineEdit()
        self.nombre = QLineEdit()
        self.apellido = QLineEdit()
        self.email = QLineEdit()
        self.fecha_nac = QDateEdit()
        self.fecha_nac.setCalendarPopup(True)
        self.fecha_nac.setDate(QDate.currentDate().addYears(-18))

        layout.addWidget(QLabel("DNI:")); layout.addWidget(self.dni)
        layout.addWidget(QLabel("Nombre:")); layout.addWidget(self.nombre)
        layout.addWidget(QLabel("Apellido:")); layout.addWidget(self.apellido)
        layout.addWidget(QLabel("Email (opcional):")); layout.addWidget(self.email)
        layout.addWidget(QLabel("Fecha de nacimiento:")); layout.addWidget(self.fecha_nac)

        btn_guardar = QPushButton("✅ Crear persona")
        btn_guardar.clicked.connect(self.validar_y_aceptar)
        layout.addWidget(btn_guardar)

        self.setLayout(layout)

    def validar_y_aceptar(self):
        dni = self.dni.text().strip()
        nombre = self.nombre.text().strip()
        apellido = self.apellido.text().strip()
        email = self.email.text().strip()

        if not all([dni, nombre, apellido]):
            QMessageBox.warning(self, "Faltan datos", "DNI, nombre y apellido son obligatorios.")
            return

        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "Email inválido", "El correo no tiene un formato válido.")
            return

        if dni_existe(dni):
            QMessageBox.critical(self, "Duplicado", "Ya existe una persona con ese DNI.")
            return

        self.datos_persona = {
            "dni": dni,
            "nombre": nombre.title(),
            "apellido": apellido.title(),
            "email": email or None,
            "fecha_nacimiento": self.fecha_nac.date().toPython()
        }
        self.accept()

    def obtener_datos(self):
        return getattr(self, "datos_persona", None)
