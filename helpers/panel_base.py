from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSizePolicy
from helpers.encabezado_widget import EncabezadoWidget
from helpers.mixin_cuenta import *
from dialogs.buscar_producto import BuscarProductoDialog
from dialogs.ver_productos import VerProductosDialog
from core.configuracion import obtener_configuracion_sistema

class BasePanel(QMainWindow, MixinCuentaUsuario):
    def __init__(self, sesion: dict, router=None):
        super().__init__()
        self.sesion = sesion
        self.router = router
        self.setMinimumSize(700, 500)
        self.setWindowTitle(self.titulo_ventana())
        self._inicializar_ui()
        self.showMaximized()
        self.config_sistema = obtener_configuracion_sistema()


    def _inicializar_ui(self):
        contenedor = QWidget()
        layout = QVBoxLayout()

        # 🧱 Header común
        encabezado = EncabezadoWidget(self.sesion)
        layout.addWidget(encabezado)

        # 🧱 Contenido específico
        self.contenido_principal(layout)

        contenedor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        # 🧱 Menú superior adaptado
        self.crear_menu()

    def crear_menu(self):
        rol = self.sesion.get("rol", "")
        callbacks = {
            "ver_datos": self.ver_datos_usuario,
            "actualizar_email": self.actualizar_email,
            "cambiar_contrasena": self.cambiar_contraseña,
            "cerrar_sesion": self.cerrar_sesion,
            "gestionar_pendientes": getattr(self, "abrir_visor_pendientes", None)
        }

        if rol == "dueño":
            MenuDueño().construir(self, callbacks)
        elif rol == "gerente":
            MenuGerente().construir(self, callbacks)
        else:
            MenuGeneral().construir(self, callbacks)

    def titulo_ventana(self):
        return "🧭 Panel"

    def contenido_principal(self, layout: QVBoxLayout):
        raise NotImplementedError("Debés implementar el contenido principal del panel")
    
    def buscar_producto(self):
        dialogo = BuscarProductoDialog(sesion=self.sesion, modo="ver")
        dialogo.exec()

    def ver_todos_los_productos(self):
        dialogo = VerProductosDialog(self.sesion, self.config_sistema)
        dialogo.exec()
