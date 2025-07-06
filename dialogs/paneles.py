from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout, QMessageBox, QLabel, QMainWindow, QDialog, QLineEdit
)
from dialogs.alta_producto import AltaProductoDialog 
from dialogs.crear_usuario import CrearUsuarioDialog
from dialogs.pendientes_producto import PendientesDeAprobacion
from helpers.mixin_cuenta import *
from helpers.panel_base import *

class PanelRepositor(BasePanel):
    def titulo_ventana(self):
        return "📦 Panel de Repositor"

    def contenido_principal(self, layout: QVBoxLayout):
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton

        box = QGroupBox("🧾 Reposición de stock")
        inner = QVBoxLayout()

        btn1 = QPushButton("➕ Alta de producto")
        btn1.clicked.connect(self.alta_producto)
        inner.addWidget(btn1)

        btn2 = QPushButton("📥 Registrar reposición")
        inner.addWidget(btn2)

        btn3 = QPushButton("📚 Ver historial")
        inner.addWidget(btn3)

        box.setLayout(inner)
        layout.addWidget(box)

    def alta_producto(self):
        dialogo = AltaProductoDialog(self.sesion)
        dialogo.exec()

    def ver_stock_bajo(self):
        QMessageBox.information(self, "Stock bajo", "👉 Aquí se mostrarán los productos con stock crítico.")

    def registrar_reposicion(self):
        QMessageBox.information(self, "Reposición", "👉 Aquí se podrá seleccionar un producto y registrar reposición.")

    def ver_historial(self):
        QMessageBox.information(self, "Historial", "👉 Acá se mostrará el historial de reposiciones realizadas.")
        
        
class PanelGerente(PanelRepositor):
    def titulo_ventana(self):
        return "🧑‍💼 Panel de Gerente"

    def contenido_principal(self, layout: QVBoxLayout):
        super().contenido_principal(layout)

        box = QGroupBox("📋 Gestión especial del gerente")
        inner = QVBoxLayout()

        btn_pendientes = QPushButton("🟡 Aprobar productos pendientes")
        btn_pendientes.clicked.connect(self.gestionar_pendientes)
        inner.addWidget(btn_pendientes)

        btn_stats = QPushButton("📈 Ver estadísticas")
        btn_stats.clicked.connect(self.ver_estadisticas)
        inner.addWidget(btn_stats)

        box.setLayout(inner)
        layout.addWidget(box)

    def gestionar_pendientes(self):
        QMessageBox.information(self, "Productos pendientes", "👉 Aquí se mostrarán productos para aprobar.")

    def ver_estadisticas(self):
        QMessageBox.information(self, "Estadísticas", "📊 Próximamente: estadísticas de stock y rotación.")


class PanelDueño(PanelGerente):
    def titulo_ventana(self):
        return "👑 Panel de Dueño"

    def contenido_principal(self, layout):
        super().contenido_principal(layout)

        # 🔐 Sección adicional exclusiva del dueño
        box_admin = QGroupBox("⚙️ Administración avanzada")
        inner = QVBoxLayout()

        btn_auditoria = QPushButton("📊 Ver auditoría")
        btn_auditoria.clicked.connect(self.ver_auditoria)
        inner.addWidget(btn_auditoria)

        box_admin.setLayout(inner)
        layout.addWidget(box_admin)

        # 🧩 Próximamente: estadísticas, parámetros, etc.

    def abrir_visor_pendientes(self):
        visor = PendientesDeAprobacion(self.sesion)
        visor.show()

    def abrir_crear_usuario(self):
        dialogo = CrearUsuarioDialog(self.sesion)
        dialogo.exec()

    # 📊 Menú “Administración” en MenuDueño busca estos métodos:
    def gestionar_usuarios(self):
        self.abrir_crear_usuario()  # O reemplazá con un panel más completo en el futuro

    def gestionar_roles(self):
        QMessageBox.information(self, "Roles", "🔐 Gestión de roles: próximamente.")

    def ver_auditoria(self):
        QMessageBox.information(self, "Auditoría", "📊 Auditoría del sistema: próximamente.")

    def configurar_sistema(self):
        QMessageBox.information(self, "Configuración", "⚙️ Parámetros del sistema: próximamente.")