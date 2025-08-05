from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QDateEdit, QPushButton, QMessageBox, QWidget, QFileDialog
)
from PySide6.QtCore import QDate, Qt, QBuffer, QIODevice, Signal
from PySide6.QtGui import QPixmap
from core.personas import actualizar_foto_persona, dni_existe
from modulos.camara import capturar_foto
import re

class PersonaDialog(QDialog):
    persona_actualizada = Signal(dict)  # Señal para emitir los datos actualizados
    def __init__(self, modo="crear", persona=None):
        super().__init__()
        self.modo = modo
        self.persona = persona or {}
        self.setWindowTitle("✏️ Editar persona" if modo == "editar" else "👤 Nueva persona")
        self.setMinimumSize(400, 300)
        self.setup_ui()
        

    def setup_ui(self):
        
        form_layout = QVBoxLayout()

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

        form_layout.addWidget(QLabel("DNI:")); form_layout.addWidget(self.dni)
        form_layout.addWidget(QLabel("Nombre:")); form_layout.addWidget(self.nombre)
        form_layout.addWidget(QLabel("Apellido:")); form_layout.addWidget(self.apellido)
        form_layout.addWidget(QLabel("Email (opcional):")); form_layout.addWidget(self.email)
        form_layout.addWidget(QLabel("Fecha de nacimiento:")); form_layout.addWidget(self.fecha_nac)

        btn_guardar = QPushButton("✅ Guardar cambios" if self.modo == "editar" else "✅ Crear persona")
        btn_guardar.clicked.connect(self.validar_y_aceptar)
        form_layout.addWidget(btn_guardar)

        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        

        # if self.modo == "editar":
        #     self.dni.setDisabled(True)
            
        self.setLayout(form_layout)


    def validar_y_aceptar(self):
        dni = self.dni.text().strip()
        nombre = self.nombre.text().strip()
        apellido = self.apellido.text().strip()
        email = self.email.text().strip()
        person_id = self.persona.get("id")

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
            "id": person_id,
            "dni": dni,
            "nombre": nombre.title(),
            "apellido": apellido.title(),
            "email": email or None,
            "fecha_nacimiento": self.fecha_nac.date().toPython()
        }

        
        self.persona_actualizada.emit(self.datos_persona)
        self.accept()

    def obtener_datos(self):
        return getattr(self, "datos_persona", None)
