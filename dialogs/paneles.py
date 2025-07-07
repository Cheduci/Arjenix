from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout, QMessageBox, QLabel, QMainWindow, QDialog, QLineEdit,
    QGridLayout
)
from dialogs.alta_producto import AltaProductoDialog 
from dialogs.crear_usuario import CrearUsuarioDialog
from dialogs.pendientes_producto import PendientesDeAprobacion
from dialogs.estadisticas_stock import EstadisticasStockDialog
from dialogs.gestor_usuarios import GestorUsuariosDialog
from dialogs.gestionar_categorias import GestionarCategoriasDialog
from dialogs.buscar_producto import BuscarProductoDialog
from dialogs.ver_productos import VerProductosDialog
from dialogs.ranking_ventas import RankingVentasDialog
from dialogs.iniciar_venta import IniciarVentaDialog
from helpers.mixin_cuenta import *
from helpers.panel_base import *

class PanelVendedor(BasePanel):
    def titulo_ventana(self):
        return "🛒 Panel de Vendedor"

    def contenido_principal(self, layout):
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QPushButton

        # 📦 Gestión de productos
        box_productos = QGroupBox("📦 Productos")
        inner = QVBoxLayout()

        btn_ver_todos = QPushButton("📋 Ver todos los productos")
        btn_ver_todos.clicked.connect(self.ver_todos_los_productos)
        inner.addWidget(btn_ver_todos)

        btn_buscar = QPushButton("🔎 Buscar producto")
        btn_buscar.clicked.connect(self.buscar_producto)
        inner.addWidget(btn_buscar)

        box_productos.setLayout(inner)
        layout.addWidget(box_productos)

        # 🛍️ Ventas 
        box_ventas = QGroupBox("🛍️ Ventas")
        inner = QVBoxLayout()

        btn_nueva_venta = QPushButton("🛒 Iniciar venta")
        btn_nueva_venta.clicked.connect(self.iniciar_venta)
        inner.addWidget(btn_nueva_venta)

        box_ventas.setLayout(inner)
        layout.addWidget(box_ventas)
    
    def buscar_producto(self):
        dialogo = BuscarProductoDialog(sesion=self.sesion, modo="ver")
        dialogo.exec()

    def ver_todos_los_productos(self):
        dialogo = VerProductosDialog(self.sesion)
        dialogo.exec()
    
    def iniciar_venta(self):
        dialogo = IniciarVentaDialog(self.sesion)
        dialogo.exec()



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
        
        
class PanelGerente(PanelRepositor, PanelVendedor):
    def titulo_ventana(self):
        return "🧑‍💼 Panel de Gerente"

    def contenido_principal(self, layout):
        # Llamamos primero a la lógica compartida
        PanelVendedor.contenido_principal(self, layout)
        PanelRepositor.contenido_principal(self, layout)

        box = QGroupBox("📋 Gestión especial del gerente")
        inner = QVBoxLayout()

        btn_pendientes = QPushButton("🟡 Aprobar productos pendientes")
        btn_pendientes.clicked.connect(self.gestionar_pendientes)
        inner.addWidget(btn_pendientes)

        btn_stats = QPushButton("📈 Ver estadísticas de stock")
        btn_stats.clicked.connect(self.ver_estadisticas)
        inner.addWidget(btn_stats)

        btn_ranking = QPushButton("🏆 Ranking de productos vendidos")
        btn_ranking.clicked.connect(self.ver_ranking_ventas)
        inner.addWidget(btn_ranking)

        box.setLayout(inner)
        layout.addWidget(box)

    def gestionar_pendientes(self):
        visor = PendientesDeAprobacion(self.sesion)
        visor.exec()

    def ver_estadisticas(self):
        dialogo = EstadisticasStockDialog(self.sesion)
        dialogo.exec()

    def ver_ranking_ventas(self):
        dialogo = RankingVentasDialog()
        dialogo.exec()

class PanelDueño(PanelGerente):
    def titulo_ventana(self):
        return "👑 Panel de Dueño"

    def contenido_principal(self, layout):
        super().contenido_principal(layout)

        # 👥 Gestión de usuarios
        box_usuarios = QGroupBox("👥 Gestión de usuarios")
        inner = QVBoxLayout()

        btn_crear = QPushButton("👤 Crear nuevo usuario")
        btn_crear.clicked.connect(self.abrir_crear_usuario)
        inner.addWidget(btn_crear)

        btn_gestionar = QPushButton("🛠️ Editar usuarios existentes")
        btn_gestionar.clicked.connect(self.abrir_gestor_usuarios)
        inner.addWidget(btn_gestionar)

        box_usuarios.setLayout(inner)
        layout.addWidget(box_usuarios)

        # 🔐 Sección adicional exclusiva del dueño
        box_admin = QGroupBox("⚙️ Administración avanzada")
        inner = QVBoxLayout()

        btn_auditoria = QPushButton("📊 Ver auditoría")
        btn_auditoria.clicked.connect(self.ver_auditoria)
        inner.addWidget(btn_auditoria)

        btn_categorias = QPushButton("🗂️ Gestionar categorías")
        btn_categorias.clicked.connect(self.abrir_gestion_categorias)
        inner.addWidget(btn_categorias)


        box_admin.setLayout(inner)
        layout.addWidget(box_admin)

    def abrir_visor_pendientes(self):
        visor = PendientesDeAprobacion(self.sesion)
        visor.show()

    def abrir_crear_usuario(self):
        dialogo = CrearUsuarioDialog(self.sesion)
        dialogo.exec()

    def abrir_gestor_usuarios(self):
        GestorUsuariosDialog(self.sesion).exec()

    def abrir_gestion_categorias(self):
        dialogo = GestionarCategoriasDialog()
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