from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QDialog, QMessageBox, QHBoxLayout, QLineEdit
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from bbdd.db_config import conectar_db
from helpers import validators
from dialogs.cambio_password import CambioPasswordDialog

class MixinCuentaUsuario:
    def ver_datos_usuario(self):
        datos = self.sesion
        dialogo = QDialog(self)
        dialogo.setWindowTitle("👤 Mis datos")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"🆔 Usuario: {datos['username']}"))
        layout.addWidget(QLabel(f"📛 Nombre: {datos.get('nombre', '')} {datos.get('apellido', '')}"))
        layout.addWidget(QLabel(f"📧 Email: {datos.get('email', 'No registrado')}"))
        layout.addWidget(QLabel(f"🛡️ Rol: {datos['rol']}"))
        dialogo.setLayout(layout)
        dialogo.exec()

    def actualizar_email(self):
        class EmailDialog(QDialog):
            def __init__(self, sesion):
                super().__init__()
                self.sesion = sesion
                self.setWindowTitle("📧 Actualizar email")
                layout = QVBoxLayout()
                self.email_input = QLineEdit()
                layout.addWidget(QLabel("Nuevo correo electrónico:"))
                layout.addWidget(self.email_input)
                btn = QPushButton("Actualizar")
                btn.clicked.connect(self.actualizar)
                layout.addWidget(btn)
                self.setLayout(layout)

            def actualizar(self):
                email = self.email_input.text().strip()
                if not validators.validar_email(email):
                    QMessageBox.warning(self, "Correo inválido", "El correo ingresado no es válido.")
                    return
                try:
                    conn = conectar_db()
                    cur = conn.cursor()
                    cur.execute("UPDATE personas SET email = %s WHERE id = %s", (email, self.sesion["persona_id"]))
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "Éxito", "Correo actualizado.")
                    self.accept()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        EmailDialog(self.sesion).exec()

    def cambiar_contraseña(self):
        dialogo = CambioPasswordDialog(self.sesion)
        dialogo.exec()

    def cerrar_sesion(self):
        self.router.cerrar_sesion()

class MenuGeneral:
    def construir(self, ventana, callbacks):
        bar = ventana.menuBar()
        perfil = bar.addMenu("Perfil")
        perfil.addAction("Ver mis datos", callbacks["ver_datos"])
        perfil.addAction("Actualizar email", callbacks["actualizar_email"])
        perfil.addAction("Cambiar contraseña", callbacks["cambiar_contrasena"])

        config = bar.addMenu("Configuración")
        config.addAction("Modo oscuro (próximamente)")

        sesion = bar.addMenu("Sesión")
        sesion.addAction("Cerrar sesión", callbacks["cerrar_sesion"])

class MenuGerente(MenuGeneral):
    def construir(self, ventana, callbacks):
        super().construir(ventana, callbacks)

        menu_gestion = ventana.menuBar().addMenu("Gestión")

        if callbacks.get("gestionar_pendientes"):
            menu_gestion.addAction("🟡 Productos pendientes", callbacks["gestionar_pendientes"])

        if callbacks.get("ver_estadisticas"):
            menu_gestion.addAction("📈 Ver estadísticas", callbacks["ver_estadisticas"])

class MenuDueño(MenuGerente):
    def construir(self, ventana, callbacks):
        super().construir(ventana, callbacks)

        menu_admin = ventana.menuBar().addMenu("Administración")

        if callbacks.get("gestionar_usuarios"):
            menu_admin.addAction("👥 Usuarios", callbacks["gestionar_usuarios"])
        if callbacks.get("gestionar_roles"):
            menu_admin.addAction("🛡️ Roles", callbacks["gestionar_roles"])
        if callbacks.get("ver_auditoria"):
            menu_admin.addAction("📊 Auditoría", callbacks["ver_auditoria"])
        if callbacks.get("configurar_sistema"):
            menu_admin.addAction("⚙️ Parámetros del sistema", callbacks["configurar_sistema"])

    