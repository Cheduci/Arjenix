from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox,
    QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from bbdd import db_config
import bcrypt
import os
from datetime import datetime
from PySide6.QtWidgets import QDateEdit
from PySide6.QtCore import QDate
from helpers import validators, exportar


class SetupInicialDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛠️ Configuración inicial — Arjenix")
        self.setFixedSize(400, 420)
        self.nombre_empresa_input = QLineEdit()
        self.slogan_input = QLineEdit()
        self.logo_button = QPushButton("Seleccionar logo")
        self.logo_preview = QLabel()
        self.logo_button.clicked.connect(self.seleccionar_logo)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("👋 Bienvenido a Arjenix"))
        layout.addWidget(QLabel("Primero debemos crear al usuario dueño."))

        empresa_layout = QFormLayout()
        empresa_layout.addRow("🏢 Nombre empresa:", self.nombre_empresa_input)
        empresa_layout.addRow("💬 Slogan (opcional):", self.slogan_input)
        empresa_layout.addRow("🖼️ Logo:", self.logo_button)
        empresa_layout.addRow(self.logo_preview)

        layout.addLayout(empresa_layout)

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
        self.confirmar_password = QLineEdit()
        self.confirmar_password.setEchoMode(QLineEdit.Password)

        form.addRow("🆔 DNI*:", self.dni)
        form.addRow("🧑 Nombre*:", self.nombre)
        form.addRow("👤 Apellido*:", self.apellido)
        form.addRow("📧 Email:", self.email)
        form.addRow("📅 Fecha nacimiento:", self.fecha_nac)
        form.addRow("🔐 Usuario*:", self.username)
        form.addRow("🔑 Contraseña*:", self.password)
        form.addRow("🗝️ Confirmar contraseña*:", self.confirmar_password)

        layout.addLayout(form)

        self.btn_crear = QPushButton("Crear dueño")
        self.btn_crear.clicked.connect(self.crear_duenio)
        layout.addWidget(self.btn_crear)

        self.setLayout(layout)
    
    def crear_duenio(self):
        datos = {
            "dni": self.dni.text().strip(),
            "nombre": self.nombre.text().strip().title(),
            "apellido": self.apellido.text().strip().title(),
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

        if self.password.text().strip() != self.confirmar_password.text().strip():
            QMessageBox.warning(self, "Contraseñas no coinciden", "La confirmación no coincide con la contraseña.")
            return
        
        if fecha_obj > datetime.today().date():
            QMessageBox.warning(self, "Fecha inválida", "La fecha de nacimiento no puede estar en el futuro.")
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

            nombre_empresa = self.nombre_empresa_input.text().strip()
            slogan = self.slogan_input.text().strip()
            logo_bytes = getattr(self, "logo_data", None)

            if logo_bytes is None and hasattr(self, "logo_path"):
                try:
                    with open(self.logo_path, "rb") as f:
                        logo_bytes = f.read()
                except Exception:
                    logo_bytes = None  # fallback silencioso

            if nombre_empresa:
                cur.execute("""
                    INSERT INTO configuracion_empresa (nombre, slogan, logo)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (nombre_empresa, slogan or None, logo_bytes))

            conn.commit()
            conn.close()

            ruta_pdf = os.path.join(os.getcwd(), "exportaciones/credenciales/credenciales_iniciales.pdf")
            exportar.exportar_credenciales_basicas(ruta_pdf, datos["username"], datos["password"], rol="dueño")

            QMessageBox.information(self, "Usuario creado", "✅ Dueño creado con éxito. ¡Bienvenido!")
            QMessageBox.information(self, "PDF generado", f"Se exportó un PDF con las credenciales en:\n{ruta_pdf}")
            self.accept()  # Cerramos el diálogo con éxito
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario.\n{e}")
        finally:
            if conn:
                conn.close()

    def seleccionar_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self.logo_path = path
            with open(path, "rb") as f:
                self.logo_data = f.read()  # esto lo vas a insertar como BYTEA
            pixmap = QPixmap(path).scaled(150, 150, Qt.KeepAspectRatio)
            self.logo_preview.setPixmap(pixmap)
    
def obtener_logo(conn):
    cur = conn.cursor()
    cur.execute("SELECT logo FROM configuracion_empresa LIMIT 1")
    result = cur.fetchone()
    if result and result[0]:
        img_bytes = result[0]
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)
        return pixmap
    return None
