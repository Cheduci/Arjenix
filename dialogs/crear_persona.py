from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QDateEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import QDate
from core.personas import dni_existe
import re

class PersonaDialog(QDialog):
    def __init__(self, modo="crear", persona=None):
        super().__init__()
        self.modo = modo
        self.persona = persona or {}
        self.setWindowTitle("✏️ Editar persona" if modo == "editar" else "👤 Nueva persona")
        self.setMinimumSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.dni = QLineEdit(self.persona.get("dni", ""))
        self.nombre = QLineEdit(self.persona.get("nombre", ""))
        self.apellido = QLineEdit(self.persona.get("apellido", ""))
        self.email = QLineEdit(self.persona.get("email") or "")

        self.fecha_nac = QDateEdit()
        self.fecha_nac.setCalendarPopup(True)
        fecha = self.persona.get("fecha_nacimiento")
        if fecha:
            self.fecha_nac.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.fecha_nac.setDate(QDate.currentDate().addYears(-18))

        layout.addWidget(QLabel("DNI:")); layout.addWidget(self.dni)
        layout.addWidget(QLabel("Nombre:")); layout.addWidget(self.nombre)
        layout.addWidget(QLabel("Apellido:")); layout.addWidget(self.apellido)
        layout.addWidget(QLabel("Email (opcional):")); layout.addWidget(self.email)
        layout.addWidget(QLabel("Fecha de nacimiento:")); layout.addWidget(self.fecha_nac)

        btn_guardar = QPushButton("✅ Guardar cambios" if self.modo == "editar" else "✅ Crear persona")
        btn_guardar.clicked.connect(self.validar_y_aceptar)
        layout.addWidget(btn_guardar)

        self.setLayout(layout)

        if self.modo == "editar":
            self.dni.setDisabled(True)

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

        if self.modo == "crear" and dni_existe(dni):
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

