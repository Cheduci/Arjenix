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
        main_layout = QHBoxLayout()
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
        main_layout.addWidget(form_widget)

        if self.modo == "editar":
            self.dni.setDisabled(True)
            panel_foto = self.setup_foto_panel()
            foto_widget = QWidget()
            foto_widget.setLayout(panel_foto)
            main_layout.addWidget(foto_widget)

        self.setLayout(main_layout)

    def setup_foto_panel(self):
        panel = QVBoxLayout()

        self.label_foto = QLabel()
        self.label_foto.setFixedSize(128, 128)
        self.label_foto.setAlignment(Qt.AlignCenter)
        self.label_foto.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f8f8f8;
                font-size: 12pt;
                color: #666;
            }
        """)

        foto_data = self.persona.get("foto")
        if foto_data:
            pixmap = QPixmap()
            pixmap.loadFromData(foto_data)
            self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.label_foto.setText("📷 Sin foto")

        btn_cargar = QPushButton("📁 Cargar")
        btn_cargar.clicked.connect(self.cargar_foto)

        btn_sacar = QPushButton("📸 Sacar foto")
        btn_sacar.clicked.connect(self.sacar_foto)

        self.btn_eliminar_foto = QPushButton("🗑️ Eliminar")
        self.btn_eliminar_foto.clicked.connect(self.eliminar_foto)
        if not foto_data:
            self.btn_eliminar_foto.setEnabled(False)

        for btn in [btn_cargar, btn_sacar, self.btn_eliminar_foto]:
            panel.addWidget(btn)

        contenedor = QVBoxLayout()
        contenedor.addWidget(self.label_foto)
        contenedor.addLayout(panel)

        return contenedor
    

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

        if self.modo == "editar":
            self.datos_persona["id"] = self.persona["id"]
            if self.persona["foto"] is not None:
                actualizar_foto_persona(
                    persona_id=self.persona["id"],  # o el ID nuevo si lo acabás de crear
                    foto_bytes=self.persona["foto"]
                )
            else:
                actualizar_foto_persona(
                    persona_id=self.persona["id"],
                    foto_bytes=None
                )
        self.persona_actualizada.emit(self.datos_persona)
        self.accept()

    def obtener_datos(self):
        return getattr(self, "datos_persona", None)

    def cargar_foto(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QPixmap(path)
            self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # 🔁 Convertir el pixmap en bytes usando QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap.save(buffer, "PNG")  # También puede ser "JPG", pero PNG preserva transparencia
            foto_bytes = bytes(buffer.data())

            # 💾 Guardar en el diccionario de la persona
            self.persona["foto"] = foto_bytes
            self.btn_eliminar_foto.setEnabled(True)

    def sacar_foto(self):
        foto_bytes = capturar_foto()
        if not foto_bytes:
            QMessageBox.warning(self, "Captura cancelada", "No se pudo obtener la foto desde la cámara.")
            return

        pixmap = QPixmap()
        pixmap.loadFromData(foto_bytes)
        self.label_foto.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.persona["foto"] = foto_bytes
        self.btn_eliminar_foto.setEnabled(True)

    def eliminar_foto(self):
        self.label_foto.clear()
        self.label_foto.setText("📷 Sin foto")
        self.persona["foto"] = None
        self.btn_eliminar_foto.setEnabled(False)