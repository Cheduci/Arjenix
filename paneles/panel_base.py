from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSizePolicy
from helpers.encabezado_widget import EncabezadoWidget
from paneles.mixin_cuenta import *
from dialogs.buscar_producto import BuscarProductoDialog
from dialogs.ver_productos import VerProductosDialog
from core.configuracion import obtener_configuracion_sistema, config_signals

class BasePanel(QMainWindow, MixinCuentaUsuario):
    def __init__(self, sesion: dict, router=None):
        super().__init__()
        self.sesion = sesion
        self.router = router
        self.config_sistema = obtener_configuracion_sistema()
        self.setMinimumSize(700, 500)
        self.setWindowTitle(self.titulo_ventana())

        # 🔄 Escuchar cambios de configuración si el panel lo necesita
        if hasattr(self, "actualizar_configuracion"):
            config_signals.configuracion_actualizada.connect(self.actualizar_configuracion)

        self._inicializar_ui()
        self.showMaximized()


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
        callbacks = self.obtener_callbacks_por_rol()

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

    def obtener_callbacks_por_rol(self) -> dict:
        base = {
            "ver_datos": self.ver_datos_usuario,
            "actualizar_email": self.actualizar_email,
            "cambiar_contrasena": self.cambiar_contraseña,
            "cerrar_sesion": self.cerrar_sesion
        }

        rol = self.sesion.get("rol", "")
        if rol == "gerente":
            base.update({
                "gestionar_pendientes": getattr(self, "gestionar_pendientes", None),
                "ver_estadisticas": getattr(self, "ver_estadisticas", None),
                "ver_ranking_ventas": getattr(self, "ver_ranking_ventas", None),
                "mostrar_reporte_diario": getattr(self, "mostrar_reporte_diario", None)
            })
        elif rol == "dueño":
            base.update({
                "gestionar_pendientes": getattr(self, "gestionar_pendientes", None),
                "ver_estadisticas": getattr(self, "ver_estadisticas", None),
                "ver_ranking_ventas": getattr(self, "ver_ranking_ventas", None),
                "mostrar_reporte_diario": getattr(self, "mostrar_reporte_diario", None),
                "gestionar_usuarios": getattr(self, "abrir_gestor_usuarios", None),
                "gestionar_roles": getattr(self, "gestionar_roles", None),
                "ver_auditoria": getattr(self, "ver_auditoria", None),
                "configurar_sistema": getattr(self, "configurar_sistema", None)
            })

        return base