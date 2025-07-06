from PySide6.QtWidgets import QApplication, QMessageBox
from bbdd.db_config import conectar_db
from login_window import LoginWindow
from modulos import setup_inicial
from modulos.paneles import PanelDueño  # 🔁 otros roles podrían ir acá también
import sys

def main():
    app = QApplication(sys.argv)

    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE;")
    tiene_usuarios = cur.fetchone()[0] > 0

    if not tiene_usuarios:
        setup = setup_inicial.SetupInicialDialog()
        if not setup.exec():
            sys.exit()  # El usuario cerró el setup sin completarlo
        # Si se completó el setup, pasamos automáticamente al login

    # Mostrar login
    login = LoginWindow()
    if not login.exec():
        sys.exit()  # Usuario cerró sin loguearse

    sesion = login.obtener_datos_sesion()
    rol = sesion.get("rol")

    # Abrir el panel correspondiente
    if rol == "dueño":
        ventana = PanelDueño(sesion)
    else:
        QMessageBox.information(None, "Sin panel", f"No hay panel disponible para el rol: {rol}")
        sys.exit()

    ventana.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
