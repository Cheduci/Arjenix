from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout
)
from modulos.visor_pendientes import PendientesDeAprobacion
from modulos.crear_usuario import CrearUsuarioDialog  # Lo armamos enseguida

class PanelDueño(QWidget):
    def __init__(self, sesion: dict):
        super().__init__()
        self.sesion = sesion
        self.setWindowTitle("👑 Panel de dueño")
        self.setMinimumSize(700, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 📦 Sección de productos
        box_stock = QGroupBox("Gestión de stock")
        layout_stock = QVBoxLayout()
        btn_pendientes = QPushButton("🟡 Ver productos pendientes de aprobación")
        btn_pendientes.clicked.connect(self.abrir_visor_pendientes)
        layout_stock.addWidget(btn_pendientes)
        box_stock.setLayout(layout_stock)
        layout.addWidget(box_stock)

        # 👥 Sección de usuarios
        box_usuarios = QGroupBox("👥 Gestión de usuarios")
        layout_usuarios = QVBoxLayout()
        btn_crear_usuario = QPushButton("👤 Crear nuevo usuario")
        btn_crear_usuario.clicked.connect(self.abrir_crear_usuario)
        layout_usuarios.addWidget(btn_crear_usuario)
        box_usuarios.setLayout(layout_usuarios)
        layout.addWidget(box_usuarios)

        self.setLayout(layout)

    def abrir_visor_pendientes(self):
        visor = PendientesDeAprobacion(self.sesion)
        visor.show()

    def abrir_crear_usuario(self):
        dialogo = CrearUsuarioDialog(self.sesion)
        dialogo.exec()
