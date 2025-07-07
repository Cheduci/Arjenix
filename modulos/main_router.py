from PySide6.QtWidgets import QApplication
from login_window import LoginWindow
from dialogs.paneles import *
from modulos import setup_inicial
import sys

class MainRouter:
    def __init__(self, arranca_con_setup=False):
        self.app = QApplication(sys.argv)
        self.sesion = None
        
        if arranca_con_setup:
            self.iniciar_con_setup()
        else:
            self.mostrar_login()

    def mostrar_login(self):
        login = LoginWindow()
        if login.exec():
            self.sesion = login.obtener_datos_sesion()
            self.mostrar_panel_principal()
        else:
            sys.exit()

    def mostrar_panel_principal(self):
        rol = self.sesion.get("rol")

        if rol == "dueño":
            self.ventana = PanelDueño(self.sesion)
        elif rol == "repositor":
            self.ventana = PanelRepositor(self.sesion)
        elif rol == "gerente":
            self.ventana = PanelGerente(self.sesion)
        elif rol == "vendedor":
            self.ventana = PanelVendedor(self.sesion)
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "Rol desconocido", f"No hay panel asignado para el rol: {rol}")
            sys.exit()

        self.ventana.router = self  # Para permitir que el panel llame a cerrar_sesion()
        self.ventana.show()
        self.app.exec()

    def cerrar_sesion(self):
        self.ventana.close()
        self.mostrar_login()

    def iniciar_con_setup(self):
        setup = setup_inicial.SetupInicialDialog()
        if setup.exec():
            self.mostrar_login()
        else:
            sys.exit()
