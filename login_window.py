from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core import auth
from modulos import cambio_password
import sys
import os

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arjenix — Ingreso al sistema")
        self.setFixedSize(400, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Logo
        logo_path = "ui/Arjenix_transparente.png"
        if os.path.exists(logo_path):
            self.logo = QLabel()
            pixmap = QPixmap(logo_path).scaledToHeight(100, Qt.SmoothTransformation)
            self.logo.setPixmap(pixmap)
            self.logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.logo)

        # Usuario
        self.usuario_input = QLineEdit()
        self.usuario_input.setPlaceholderText("Usuario")
        layout.addWidget(self.usuario_input)

        # Contraseña
        self.contra_input = QLineEdit()
        self.contra_input.setPlaceholderText("Contraseña")
        self.contra_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.contra_input)

        # Botón ingresar
        self.btn_ingresar = QPushButton("Ingresar")
        self.btn_ingresar.clicked.connect(self.login)
        layout.addWidget(self.btn_ingresar)

        self.setLayout(layout)

    def login(self):
        usuario = self.usuario_input.text().strip()
        password = self.contra_input.text().strip()

        if not usuario or not password:
            QMessageBox.warning(self, "Campos requeridos", "Ingresá usuario y contraseña.")
            return

        resultado = auth.autenticar_usuario(usuario, password)

        if resultado == "error_conexion":
            QMessageBox.critical(self, "Base de datos", "No se pudo conectar con la base.")
            return
        
        if resultado["debe_cambiar_password"]:
            dialogo = cambio_password.CambioPasswordDialog(resultado)
            if dialogo.exec():
                self.redirigir_segun_rol(resultado)
            return
        
        if not resultado:
            QMessageBox.warning(self, "Acceso denegado", "Credenciales incorrectas.")
            return

        # Éxito: redirigir según rol
        if resultado["debe_cambiar_password"]:
            self.ocultar_y_pedir_nueva_password(resultado)
        else:
            self.redirigir_segun_rol(resultado)

    def ocultar_y_pedir_nueva_password(self, sesion):
        # Próximo paso: abrir un QDialog de cambio obligatorio
        print("🔐 Debería cambiar la contraseña")  # temporal
        # TODO: Implementar diálogo
        pass

    def redirigir_segun_rol(self, sesion):
        rol = sesion["rol"]
        nombre = sesion["nombre"]
        QMessageBox.information(self, "Bienvenido", f"Hola {nombre}, ingresaste como {rol}.")
        # TODO: abrir la ventana correspondiente
        print(f"📥 Redirigir a panel de: {rol}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = LoginWindow()
    ventana.show()
    sys.exit(app.exec())
