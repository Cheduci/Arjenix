from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout, QMessageBox, QLabel, QMainWindow, QDialog, QLineEdit,
    QGridLayout, QSizePolicy, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from dialogs.alta_producto import AltaProductoDialog 
from dialogs.crear_usuario import CrearUsuarioDialog
from dialogs.pendientes_producto import PendientesDeAprobacion
from dialogs.estadisticas_stock import EstadisticasStockDialog
from dialogs.gestor_usuarios import GestorUsuariosDialog
from dialogs.gestionar_categorias import GestionarCategoriasDialog
from dialogs.ranking_ventas import RankingVentasDialog
from dialogs.iniciar_venta import IniciarVentaDialog
from helpers.mixin_cuenta import *
from helpers.panel_base import *


def crear_box_productos(parent):
    box_productos = QGroupBox("📦 Productos")
    inner = QVBoxLayout()

    btn_ver_todos = QPushButton("📋 Ver todos los productos")
    btn_ver_todos.clicked.connect(parent.ver_todos_los_productos)
    inner.addWidget(btn_ver_todos)

    btn_buscar = QPushButton("🔎 Buscar producto")
    btn_buscar.clicked.connect(parent.buscar_producto)
    inner.addWidget(btn_buscar)

    box_productos.setLayout(inner)
    return box_productos

class PanelVendedor(BasePanel):
    def __init__(self, sesion):
        super().__init__(sesion)
        self.sesion = sesion

    def titulo_ventana(self):
        return "🛒 Panel de Vendedor"

    def contenido_principal(self, layout):

        # 📦 Gestión de productos
        layout.addWidget(crear_box_productos(self))

        # 🛍️ Ventas 
        box_ventas = QGroupBox("🛍️ Ventas")
        inner = QVBoxLayout()

        btn_nueva_venta = QPushButton("🛒 Iniciar venta")
        btn_nueva_venta.clicked.connect(self.iniciar_venta)
        inner.addWidget(btn_nueva_venta)

        box_ventas.setLayout(inner)
        layout.addWidget(box_ventas)
    
    def iniciar_venta(self):
        dialogo = IniciarVentaDialog(self.sesion)
        dialogo.exec()



class PanelRepositor(BasePanel):
    def __init__(self, sesion, standalone=True):
        self.standalone = standalone
        super().__init__(sesion)
        self.sesion = sesion

    def titulo_ventana(self):
        return "📦 Panel de Repositor"

    def contenido_principal(self, layout: QVBoxLayout):
        if self.standalone:
            layout.addWidget(crear_box_productos(self))

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
    def __init__(self, sesion, router=None):
        PanelRepositor.__init__(self, sesion, standalone=False)
        self.sesion = sesion
        self.router = router

    def titulo_ventana(self):
        return "🧑‍💼 Panel de Gerente"
    
    def contenido_principal(self, layout):
        # 🧑‍💼 Panel Gerente
        box = QGroupBox("🧑‍💼 Panel de Gerente")
        inner = QHBoxLayout()
        # box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Columna vendedor
        panel_vendedor = QWidget()
        layout_vendedor = QVBoxLayout()
        panel_vendedor.setLayout(layout_vendedor)
        self.contenido_vendedor(layout_vendedor)
        inner.addWidget(panel_vendedor)

        # Columna gerente
        self.contenido_gerente(inner)

        # Columna repositor
        panel_repositor = QWidget()
        layout_repositor = QVBoxLayout()
        panel_repositor.setLayout(layout_repositor)
        self.contenido_repositor(layout_repositor)
        inner.addWidget(panel_repositor)

        box.setLayout(inner)
        layout.addWidget(box)

    def contenido_vendedor(self, layout: QVBoxLayout):
        PanelVendedor.contenido_principal(self, layout)

    def contenido_repositor(self, layout: QVBoxLayout):
        PanelRepositor.contenido_principal(self, layout)

    def contenido_gerente(self, layout: QVBoxLayout):
        box = QGroupBox("📋 Gestión gerencial")
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



class PanelAjustesSistema(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)


        box_config = QGroupBox("⚙️ Ajustes generales")
        inner_config = QVBoxLayout()
        inner_config.addStretch()

        btn_preferencias = QPushButton("🧩 Preferencias de usuario")
        btn_preferencias.clicked.connect(self.abrir_preferencias)
        inner_config.addWidget(btn_preferencias)
        inner_config.addStretch()

        btn_backup = QPushButton("💾 Respaldar base de datos")
        btn_backup.clicked.connect(self.realizar_backup)
        inner_config.addWidget(btn_backup)
        inner_config.addStretch()

        btn_mantenimiento = QPushButton("🧹 Modo mantenimiento")
        btn_mantenimiento.clicked.connect(self.activar_mantenimiento)
        inner_config.addWidget(btn_mantenimiento)
        inner_config.addStretch()

        box_config.setLayout(inner_config)
        layout.addWidget(box_config)


    def abrir_preferencias(self):
        QMessageBox.information(self, "Preferencias", "Abrir diálogo de preferencias.")

    def cambiar_tema(self):
        QMessageBox.information(self, "Tema visual", "Funcionalidad de tema aún no implementada.")

    def realizar_backup(self):
        QMessageBox.information(self, "Backup", "Iniciando respaldo...")

    def activar_mantenimiento(self):
        QMessageBox.information(self, "Mantenimiento", "Modo mantenimiento activado.")

class PanelDueño(PanelGerente):
    def __init__(self, sesion, router=None):
        super().__init__(sesion, router)
        self.sesion = sesion
        self.router = router

    def titulo_ventana(self):
        return "👑 Panel de Dueño"

    def contenido_principal(self, layout_padre):

        box = QGroupBox("👑 Panel de Dueño")
        inner = QHBoxLayout()
        # fila_paneles = QWidget()
        # layout_horizontal = QHBoxLayout(fila_paneles)
        # fila_paneles.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # layout_padre.addWidget(fila_paneles)

        gerente = PanelGerente(self.sesion, self.router)

        # Columna vendedor
        panel_vendedor = QWidget()
        layout_vendedor = QVBoxLayout()
        panel_vendedor.setLayout(layout_vendedor)
        gerente.contenido_vendedor(layout_vendedor)
        # layout_horizontal.addWidget(panel_vendedor)
        inner.addWidget(panel_vendedor)

        # Columna gerente
        panel_gerente = QWidget()
        layout_gerente = QVBoxLayout()
        panel_gerente.setLayout(layout_gerente)
        gerente.contenido_gerente(layout_gerente)
        # layout_horizontal.addWidget(panel_gerente)
        inner.addWidget(panel_gerente)

        # 👑 Panel Dueño 
        panel_duenio = QWidget()
        layout_duenio = QVBoxLayout()
        panel_duenio.setLayout(layout_duenio)
        self.contenido_exclusivo_duenio(layout_duenio)
        # layout_horizontal.addWidget(panel_duenio)
        inner.addWidget(panel_duenio)

        # 🛠️ Panel Ajustes
        panel_ajustes = PanelAjustesSistema()
        # layout_horizontal.addWidget(panel_ajustes)
        inner.addWidget(panel_ajustes)

        # Columna repositor
        panel_repositor = QWidget()
        layout_repositor = QVBoxLayout()
        panel_repositor.setLayout(layout_repositor)
        gerente.contenido_repositor(layout_repositor)
        # layout_horizontal.addWidget(panel_repositor)
        inner.addWidget(panel_repositor)

        box.setLayout(inner)
        layout_padre.addWidget(box)


    def contenido_exclusivo_duenio(self, layout):
        # 👥 Gestión de usuarios
        box_usuarios = QGroupBox("👥 Gestión de usuarios")
        inner_usuarios = QVBoxLayout()

        btn_crear = QPushButton("👤 Crear nuevo usuario")
        btn_crear.clicked.connect(self.abrir_crear_usuario)
        inner_usuarios.addWidget(btn_crear)

        btn_gestionar = QPushButton("🛠️ Editar usuarios existentes")
        btn_gestionar.clicked.connect(self.abrir_gestor_usuarios)
        inner_usuarios.addWidget(btn_gestionar)

        box_usuarios.setLayout(inner_usuarios)
        layout.addWidget(box_usuarios)

        # 🔐 Administración avanzada
        box_admin = QGroupBox("⚙️ Administración avanzada")
        inner_admin = QVBoxLayout()

        btn_auditoria = QPushButton("📊 Ver auditoría")
        btn_auditoria.clicked.connect(self.ver_auditoria)
        inner_admin.addWidget(btn_auditoria)

        btn_categorias = QPushButton("🗂️ Gestionar categorías")
        btn_categorias.clicked.connect(self.abrir_gestion_categorias)
        inner_admin.addWidget(btn_categorias)

        box_admin.setLayout(inner_admin)
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
