from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt
from bbdd import db_config
import bcrypt
import psycopg
from datetime import datetime
from PySide6.QtWidgets import QDateEdit
from PySide6.QtCore import QDate
from helpers import validators


class SetupInicialDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛠️ Configuración inicial — Arjenix")
        self.setFixedSize(400, 420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("👋 Bienvenido a Arjenix"))
        layout.addWidget(QLabel("Primero debemos crear al usuario dueño."))

        form = QFormLayout()

        self.dni = QLineEdit()
        self.nombre = QLineEdit()
        self.apellido = QLineEdit()
        self.email = QLineEdit()
        self.fecha_nac = QDateEdit()
        self.fecha_nac.setCalendarPopup(True)  # activa el calendario
        self.fecha_nac.setDisplayFormat("yyyy-MM-dd")
        self.fecha_nac.setDate(QDate(1990, 1, 1))  # valor por defecto opcional
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        form.addRow("🆔 DNI*:", self.dni)
        form.addRow("🧑 Nombre*:", self.nombre)
        form.addRow("👤 Apellido*:", self.apellido)
        form.addRow("📧 Email:", self.email)
        form.addRow("📅 Fecha nacimiento:", self.fecha_nac)
        form.addRow("🔐 Usuario*:", self.username)
        form.addRow("🔑 Contraseña*:", self.password)

        layout.addLayout(form)

        self.btn_crear = QPushButton("Crear dueño")
        self.btn_crear.clicked.connect(self.crear_duenio)
        layout.addWidget(self.btn_crear)

        self.setLayout(layout)

    def crear_duenio(self):
        datos = {
            "dni": self.dni.text().strip(),
            "nombre": self.nombre.text().strip(),
            "apellido": self.apellido.text().strip(),
            "email": self.email.text().strip() or None,
            "username": self.username.text().strip(),
            "password": self.password.text().strip()
        }
        
        fecha_obj = self.fecha_nac.date().toPython()

        if not all([datos["dni"], datos["nombre"], datos["apellido"], datos["username"], datos["password"]]):
            QMessageBox.warning(self, "Campos requeridos", "Completá todos los campos obligatorios.")
            return
        
        email = datos["email"]
        if email and not validators.validar_email(email):
            QMessageBox.warning(self, "Correo inválido", "El formato del correo electrónico no es válido.")
            return

        try:
            conn = db_config.conectar_db()
            cur = conn.cursor()

            # Crear rol 'dueño' si no existe
            cur.execute("SELECT id FROM roles WHERE nombre = 'dueño'")
            rol = cur.fetchone()
            if rol:
                rol_id = rol[0]
            else:
                cur.execute("INSERT INTO roles (nombre, descripcion) VALUES (%s, %s) RETURNING id",
                            ("dueño", "Acceso total al sistema"))
                rol_id = cur.fetchone()[0]

            # Insertar persona
            cur.execute("""
                INSERT INTO personas (dni, nombre, apellido, email, fecha_nacimiento, activo)
                VALUES (%s, %s, %s, %s, %s, TRUE) RETURNING id
            """, (datos["dni"], datos["nombre"], datos["apellido"], datos["email"], fecha_obj))
            persona_id = cur.fetchone()[0]

            # Hash y alta del usuario
            hashpw = bcrypt.hashpw(datos["password"].encode(), bcrypt.gensalt()).decode()

            cur.execute("""
                INSERT INTO usuarios (persona_id, username, password_hash, rol_id, activo, debe_cambiar_password)
                VALUES (%s, %s, %s, %s, TRUE, FALSE)
            """, (persona_id, datos["username"], hashpw, rol_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Usuario creado", "✅ Dueño creado con éxito. ¡Bienvenido!")
            self.accept()  # Cerramos el diálogo con éxito
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario.\n{e}")
