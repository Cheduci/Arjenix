from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QWidget
)
from core.personas import *
from core.usuarios import *
from core.roles import obtener_roles
from dialogs.crear_persona import CrearPersonaDialog
import bcrypt
from helpers.exportar import exportar_credenciales_basicas
import os


class CrearUsuarioDialog(QDialog):
    def __init__(self, sesion):
        super().__init__()
        self.setWindowTitle("👤 Crear usuario")
        self.setMinimumSize(500, 400)
        self.sesion = sesion
        self.personas_disponibles = obtener_personas_sin_usuario()

        self.combo_rol = QComboBox()  # Declarado una vez
        self.cargar_roles()

        if self.personas_disponibles:
            self.mostrar_formulario_de_persona_existente()
        else:
            self.confirmar_crear_persona_nueva()

    def reemplazar_layout(self, nuevo_layout: QVBoxLayout):
        anterior = self.layout()
        if anterior:
            QWidget().setLayout(anterior)
        self.setLayout(nuevo_layout)

    def cargar_roles(self):
        self.combo_rol.clear()
        for id_, nombre in obtener_roles():
            self.combo_rol.addItem(nombre, userData=id_)

    def mostrar_formulario_de_persona_existente(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Seleccionar persona:"))
        self.combo_persona = QComboBox()
        for p in self.personas_disponibles:
            texto = f"{p['apellido']}, {p['nombre']} — DNI {p['dni']}"
            self.combo_persona.addItem(texto, userData=p)
        self.combo_persona.currentIndexChanged.connect(self.sugerir_username)
        layout.addWidget(self.combo_persona)

        layout.addWidget(QLabel("Nombre de usuario:"))
        self.username = QLineEdit()
        layout.addWidget(self.username)

        layout.addWidget(QLabel("Contraseña:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        layout.addWidget(QLabel("Rol:"))
        layout.addWidget(self.combo_rol)

        btn_crear = QPushButton("Crear usuario")
        btn_crear.clicked.connect(self.confirmar_creacion_usuario)
        layout.addWidget(btn_crear)

        self.reemplazar_layout(layout)
        self.sugerir_username()

    def sugerir_username(self):
        persona = self.combo_persona.currentData()
        if persona:
            sugerencia = f"{persona['nombre'].lower()}.{persona['apellido'].lower()}"
            self.username.setText(sugerencia)

    def confirmar_creacion_usuario(self):
        persona = self.combo_persona.currentData()
        username = self.username.text().strip().lower()
        password = self.password.text()
        rol_id = self.combo_rol.currentData()

        if not all([persona, username, password, rol_id]):
            QMessageBox.warning(self, "Faltan datos", "Completá todos los campos.")
            return

        if username_existe(username):
            QMessageBox.critical(self, "Duplicado", "Ese nombre de usuario ya existe.")
            return

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        if crear_usuario(persona["id"], username, password_hash, rol_id):
            QMessageBox.information(self, "Usuario creado", "🟢 Usuario registrado correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar el usuario.")

    def confirmar_crear_persona_nueva(self):
        respuesta = QMessageBox.question(
            self,
            "Crear nueva persona",
            "🟡 No hay personas sin usuario asignado.\n¿Deseás crear una nueva persona ahora?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            dialogo = CrearPersonaDialog()
            if dialogo.exec():
                persona = dialogo.obtener_datos()
                persona["username_sugerido"] = f"{persona['nombre'].lower()}.{persona['apellido'].lower()}"
                persona_id = insertar_persona(persona)
                self.persona_id = persona_id
                self.mostrar_formulario_de_usuario_sobre(persona)

    def mostrar_formulario_de_usuario_sobre(self, persona: dict):
        self.setWindowTitle("👤 Asignar usuario a nueva persona")
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Creando usuario para: {persona['nombre']} {persona['apellido']} — DNI {persona['dni']}"))

        layout.addWidget(QLabel("Nombre de usuario:"))
        self.username = QLineEdit()
        self.username.setText(persona["username_sugerido"])
        layout.addWidget(self.username)

        layout.addWidget(QLabel("Contraseña:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password)

        layout.addWidget(QLabel("Rol:"))
        layout.addWidget(self.combo_rol)

        btn_crear = QPushButton("Crear usuario")
        btn_crear.clicked.connect(self.confirmar_creacion_usuario_nuevo)
        layout.addWidget(btn_crear)

        self.reemplazar_layout(layout)

    def confirmar_creacion_usuario_nuevo(self):
        username = self.username.text().strip().lower()
        password = self.password.text()
        rol_id = self.combo_rol.currentData()

        if not all([self.persona_id, username, password, rol_id]):
            QMessageBox.warning(self, "Faltan datos", "Completá todos los campos.")
            return

        if username_existe(username):
            QMessageBox.critical(self, "Duplicado", "Ese nombre de usuario ya existe.")
            return

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        if crear_usuario(self.persona_id, username, password_hash, rol_id):
            ruta = os.path.join(os.getcwd(), f"exportaciones/credenciales/credenciales_{username}.pdf")
            exportar_credenciales_basicas(ruta, username, password, rol=self.combo_rol.currentText())

            QMessageBox.information(self, "Credenciales exportadas", f"Se guardó un PDF con los datos en:\n{ruta}")
            QMessageBox.information(self, "Usuario creado", "🟢 Usuario registrado correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar el usuario.")
